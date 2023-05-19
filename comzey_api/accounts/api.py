from re import T
from datetime import timedelta,date
import re
import unicodedata
import json
import time
import datetime
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordResetForm, UserModel
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.views import PasswordContextMixin, PasswordResetView
from django.contrib.sites.shortcuts import get_current_site
from django.template import context
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.utils.translation import gettext_lazy as _
from django.views.generic.edit import BaseFormView, FormMixin
from rest_framework import ( exceptions, mixins, serializers, status,
                            viewsets)
from rest_framework.decorators import action, permission_classes
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from accounts.models import InductionAnswers, InductionQuestions, Invite, Occupation, User
from accounts.serializers import ChangePasswordSerializer, InductionAnswersListSerializer, InductionAnswersSerializer, InductionQuestionSerializer, InviteListSerializer, InviteSerializer, InviteWorkerSerializer, LoginSerializer, LoginUpdateSerializer, OccupationSerializer, ProfileDetailsUpdateSerializer, RegistrationSerializer, SendMailSerializer
from api.models import Project 
from comzey_api.custom_permissions import IsBuilder
# from api.serializers import FCMSerializer
from comzey_api.notifications import payload, send_notification
from django.core.mail import send_mail
from decouple import config
from django.shortcuts import render
from comzey_api.notifications import subscribe
from django.template.loader import render_to_string
from django.core.mail.message import EmailMultiAlternatives
from mailjet_rest import Client
from comzey_api.salesforce import salesforce
from projectnotifications.serializers import FCMSerializer
from rest_framework_jwt.authentication import JSONWebTokenAuthentication


# Create your views here.
# includes--------------->>>>>>>>>RegisterViewset, InviteViewset, TokenAuthViewset, OccupationViewset, 
# PasswordResetViewset, ProfileDetailsViewset, ChangePasswordViewset, InductionQuestionsViewset, 
# InductionAnswersViewset
class RegisterViewset(viewsets.GenericViewSet, mixins.CreateModelMixin, mixins.UpdateModelMixin):
    permission_classes = [AllowAny]
    serializer_class = RegistrationSerializer
    queryset = User.objects.none()

    def ensure_identification(self):
        data = self.request.data
        email_check= data.get('email').lower()
        if email_check:
            return True
        if data.get('facebook_token'):
            return True
        if data.get('apple_token'):
            return True
        if data.get('google_token'):
            return True
        return False
    
    def check_duplicate_tokens(self):
        data = self.request.data
        if data.get('facebook_token'):
            if User.objects.filter(facebook_token=data.get('facebook_token')).exists():
                return True
        if data.get('apple_token'):
            if User.objects.filter(apple_token=data.get('apple_token')).exists():
                return True
        if data.get('google_token'):
            if User.objects.filter(google_token=data.get('google_token')).exists():
                return True
        return False

    def create(self, request, *args, **kwargs):
        data = self.request.data
        email_check= data.get('email').lower()
        if data.get('user_type')=="builder":
            if self.ensure_identification():
                if email_check:
                    data_email = email_check
                    if self.check_duplicate_tokens():
                            return Response(data='User with this social login method already exists.', status=status.HTTP_401_UNAUTHORIZED)
                    if not (data.get('password') or data.get('facebook_token') or data.get('apple_token') or data.get('google_token')):
                        return Response(data='Password may not be blank .', status=status.HTTP_400_BAD_REQUEST)                   
                    if User.objects.filter(email=data_email).exists():
                        instance = User.objects.get(email=data_email)
                        serializer = self.get_serializer(instance, data=request.data)
                        serializer.is_valid(raise_exception=True)
                        # self.perform_update(serializer)
                        return Response(data="User with these credentials already exists.", status=status.HTTP_401_UNAUTHORIZED)
                request.data['email']=email_check
                serializer = self.get_serializer(data=request.data)
                serializer.is_valid(raise_exception=True)
                self.perform_create(serializer)
                ret_dict = dict(serializer.data.items())
                inst=Occupation.objects.get(id=request.data['occupation'])
                inst = {'id':inst.id,'name':inst.name}
                ret_dict['occupation'] = inst
                ret_dict['is_subscription']="TRIAL"
                headers = self.get_success_headers(serializer.data)
                subscribe(username=ret_dict.get('username'),id=ret_dict.get('id'))
                switch="SIGNUP"
                try:
                    payload_data={"EventType": "builder",
                    "EventAction": "new",
                    "AppCustomerId": ret_dict.get('id'),
                    "BuilderId": ret_dict.get('id'),
                    "FirstName": ret_dict.get('first_name'),
                    "LastName": ret_dict.get('last_name'),
                    "Email": ret_dict.get('email'),
                    "Phone": ret_dict.get('phone'),
                    "SignUpDate": User.objects.get(pk=ret_dict.get('id')).created_date.date().strftime(
                        "%d/%m/%Y"),
                    "Company":ret_dict.get('company'),
                    "Occupation":ret_dict.get('occupation').get('name')
                    }
                    salesforce(switch,payload_data,request)
                    return Response(ret_dict,status=status.HTTP_201_CREATED, headers=headers)
                except Exception as e:
                    print(e)
                    return Response(ret_dict,status=status.HTTP_201_CREATED, headers=headers)
            else:
                return Response('No identification parameters found.', status=status.HTTP_401_UNAUTHORIZED)
        else:
#____________________________user is already sign up but here is the updations 
            invite_id = data.get('invite_id')
            if not invite_id:
                return Response(data='No invitation Id found. Did you mean to register as an builder?',status=status.HTTP_400_BAD_REQUEST)
            obj_invite= Invite.objects.get(id=invite_id)
            user_instance=User.objects.get(invite_id=invite_id)
            # request.data._mutable=True
            request.data['invite_message']=""
            request.data['trial_ended']=date.today()+timedelta(days=30)
            user_serializer = RegistrationSerializer(user_instance,data=(request.data))
            user_serializer.is_valid(raise_exception=True)
            user_serializer.save_user(instance=user_instance,validated_data=(request.data),context={'password': request.data['password']})
            ret_dict = dict(user_serializer.data.items())
            inst=Occupation.objects.get(id=request.data['occupation'])
            inst = {'id':inst.id,'name':inst.name}
            ret_dict['occupation'] = inst
            ret_dict['is_subscription']="TRIAL"
            if user_serializer.data.get('user_type')=='worker':
                induction=User.objects.get(pk=user_serializer.data.get('id'))
                induction.is_induction=True
                induction.save()
            headers = self.get_success_headers(user_serializer.data)
            subscribe(username=ret_dict.get('username'),id=ret_dict.get('id'))  
            invite_serializer=InviteSerializer(instance=obj_invite)
            invite_serializer.update(instance=obj_invite, validated_data={'status':'accepted'})
            switch="SIGNUP"
            if ret_dict.get('user_type')=="client":
                try:
                        payload_data={"EventType": ret_dict.get('user_type'),
                        "EventAction": "new",
                        "AppCustomerId": ret_dict.get('id'),
                        "ClientId": ret_dict.get('id'),
                        "FirstName": ret_dict.get('first_name'),
                        "LastName": ret_dict.get('last_name'),
                        "Email": ret_dict.get('email'),
                        "Phone": ret_dict.get('phone'),
                        "SignUpDate": User.objects.get(pk=ret_dict.get('id')).created_date.date().strftime(
                            "%d/%m/%Y"),
                        "Company":ret_dict.get('company'),
                        "Occupation":ret_dict.get('occupation').get('name')
                        }
                        salesforce(switch,payload_data,request)
                except Exception as e:
                        print(e)
            if  ret_dict.get('user_type')=="worker":
                try:
                        payload_data={"EventType": ret_dict.get('user_type'),
                        "EventAction": "new",
                        "AppCustomerId": ret_dict.get('id'),
                        "WorkerId": ret_dict.get('id'),
                        "FirstName": ret_dict.get('first_name'),
                        "LastName": ret_dict.get('last_name'),
                        "Email": ret_dict.get('email'),
                        "Phone": ret_dict.get('phone'),
                        "SignUpDate": User.objects.get(pk=ret_dict.get('id')).created_date.date().strftime(
                            "%d/%m/%Y"),
                        "Company":ret_dict.get('company'),
                        "Occupation":ret_dict.get('occupation').get('name')
                        }
                        salesforce(switch,payload_data,request)
                except Exception as e:
                        print(e)
            if user_serializer.data.get('user_type')=='client':
                try:
                    notification_data={'title':'Invitation Accepted',
                    'sender_id':user_serializer.data.get('id'),
                    'receiver_id':Invite.objects.get(pk=invite_id).invited_by.id,
                    'notification_type':"invite_accepted_client",
                    'message':" Your invited client %s %s has registered on Build EZI.You can add %s on project"%(user_serializer.data.get('first_name'),user_serializer.data.get('last_name'),user_serializer.data.get('first_name'))}
                    notification=FCMSerializer(data=notification_data)
                    notification.is_valid(raise_exception=True)
                    notification.save()
                    data_object= {
                            "title": "Invitation Accepted",
                            "message":"Your invited client %s %s has registered on Build EZI.You can add %s on project"%(user_serializer.data.get('first_name'),user_serializer.data.get('last_name'),user_serializer.data.get('first_name')),
                            "notification_type":"invite_accepted_client",
                            'receiver_id':Invite.objects.get(pk=invite_id).invited_by.id,
                            "sender_id":user_serializer.data.get('id'),
                            "fromNotification":True
                    }
                    send_notification(User.objects.get(pk=notification_data.get("receiver_id")),data_object.get("title"),data_object.get("message"),data_object,request)
                    # return Response(data=user_serializer.data,status=status.HTTP_201_CREATED)
                    return Response(ret_dict,status=status.HTTP_201_CREATED, headers=headers)
                except Exception as e:
                        print(e)
                        return Response(ret_dict,status=status.HTTP_201_CREATED, headers=headers)
            else:
                try:
                    notification_data={'title':'Invitation Accepted',
                    'sender_id':user_serializer.data.get('id'),
                    'receiver_id':Invite.objects.get(pk=invite_id).invited_by.id,
                    'notification_type':"invite_accepted_worker",
                    'project':Invite.objects.get(pk=invite_id).project.id,
                    'message':" Your invited worker %s %s has registered on Build EZI.You can add %s on project"%(user_serializer.data.get('first_name'),user_serializer.data.get('last_name'),user_serializer.data.get('first_name'))}
                    notification=FCMSerializer(data=notification_data)
                    notification.is_valid(raise_exception=True)
                    notification.save()
                    data_object= {
                            "title": "Invitation Accepted",
                            "message":"Your invited worker %s %s has registered on Build EZI.You can add %s on project"%(user_serializer.data.get('first_name'),user_serializer.data.get('last_name'),user_serializer.data.get('first_name')),
                            "notification_type":"invite_accepted_worker",           
                            'receiver_id':Invite.objects.get(pk=invite_id).invited_by.id,
                            "sender_id":user_serializer.data.get('id'),  
                            "project_id":Invite.objects.get(pk=invite_id).project.id,
                            "fromNotification":True
                    }
                    send_notification(User.objects.get(pk=notification_data.get("receiver_id")),data_object.get("title"),data_object.get("message"),data_object,request)
                    return Response(ret_dict,status=status.HTTP_201_CREATED, headers=headers)
                except Exception as e:
                        print(e)
                        return Response(ret_dict,status=status.HTTP_201_CREATED, headers=headers)

    @action(methods=['delete'], detail=True, url_path="")
    def delete(self, request, *args, **kwargs):
        requested_user = User.objects.get(pk=self.request.user.id)
        if requested_user == self.request.user:
            user=User.objects.get(pk=self.request.user.id)
            user.message="User doesn't Exists."
            user.save()
            return Response(data="User Successfully Deleted", status=status.HTTP_200_OK)
        else:
            return Response(data="User Deletion Failed", status=status.HTTP_402_PAYMENT_REQUIRED)

class InviteViewset(viewsets.GenericViewSet, mixins.CreateModelMixin,mixins.RetrieveModelMixin,mixins.ListModelMixin):
    permission_classes=[IsBuilder]
    def get_queryset(self):
        if self.action=='list':
                return Invite.objects.filter(invited_by=self.request.user.id) 
        return User.objects.none()
    def get_serializer_class(self):
        if self.action == 'email':
            return SendMailSerializer
        if self.action == 'list':
            return InviteListSerializer
        return InviteSerializer

    def create(self, request, *args, **kwargs):
        email_check= request.data.get('email').lower()
        if email_check:
                data_email = email_check
                if  User.objects.filter(email=data_email).exists() and Invite.objects.filter(email=data_email).exists():
                    return Response(data="This user is already registered on Build EZI as %s.Please try again with different email."%(User.objects.get(email=data_email).user_type), status=status.HTTP_401_UNAUTHORIZED)
                elif User.objects.filter(email=data_email).exists() :   
                    return Response(data="This user is already registered on Build EZI as %s.Please try again with different email."%(User.objects.get(email=data_email).user_type), status=status.HTTP_401_UNAUTHORIZED)
                elif Invite.objects.filter(email=data_email).exists():
                    return Response(data="This user is already invited.Please wait for them to complete registration", status=status.HTTP_401_UNAUTHORIZED)
                elif self.request.data.get('project'):
                        if self.request.data.get('user_type')=='worker':
#____________________________user is signing up here but  he has not accepted the invite                         
                                serializer = InviteWorkerSerializer(data=request.data, context={'invited_by': request.user.id})
                                serializer.is_valid(raise_exception=True)   
                                invite_obj=serializer.save()
                                register_data=request.data
                                register_data['invite_message']="Invite_not_accepted"
                                register_data['occupation']=1
                                register_data['invite_id']=serializer.data.get('id')
                                register_data['company']="Infostride"
                                register_data['password']='Welcome@123'
                                user_serializer = RegistrationSerializer(data=register_data)
                                user_serializer.is_valid(raise_exception=True)
                                user_serializer.save()
                                project = Project.objects.get(pk=request.data.get('project') )
                                worker = User.objects.get(pk=user_serializer.data.get('id'))
                                project.worker.add(worker)
                                project.save()
                                print(user_serializer.data)
                                return Response(data=serializer.data,status=status.HTTP_200_OK)
                        return Response(data='you are specifying project.Did you mean to register as an builder or client?',status=status.HTTP_400_BAD_REQUEST)
                
                elif not self.request.data.get('project') and self.request.data.get('user_type')=='client':
                        serializer = InviteSerializer(data=request.data, context={'invited_by': request.user.id})
                        serializer.is_valid(raise_exception=True)   
                        invite_obj=serializer.save()
                        register_data=request.data
                        register_data['invite_message']="Invite_not_accepted"
                        register_data['occupation']=1
                        register_data['invite_id']=serializer.data.get('id')
                        register_data['company']="Infostride"
                        register_data['password']='Welcome@123'
                        user_serializer = RegistrationSerializer(data=register_data)
                        user_serializer.is_valid(raise_exception=True)
                        self.perform_create(user_serializer)
                        print(user_serializer.data)
                        return Response(data=serializer.data,status=status.HTTP_200_OK)
                else:
                    return Response(data='No specify user_type.Did you mean to register as an builder or client?',status=status.HTTP_400_BAD_REQUEST)
    def retrieve(self, request, pk, *args, **kwargs):
        obj = Invite.objects.get(invite_id=pk)
        serializer = self.serializer_class(instance=obj)
        if obj.status!='pending':
            return Response(status=status.HTTP_403_FORBIDDEN,data='Invite already %s.'%obj.accepted)      
        context={'invite_id':pk,'first_name':serializer.data['first_name'],'last_name':serializer.data['last_name'],'user_type':serializer.data['user_type'],'email':serializer.email_check,'occupations':Occupation.objects.all()}
        return render(request,'invite_form.html',context)

    @action(methods=['POST'],detail=False,url_path='email',url_name='email')
    def email(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if self.request.data.get('invite_id'):
                data_email = Invite.objects.get(id=request.data.get('invite_id')).email
                # (not needed)---------------------->>>>>>>>>>>>
                # if User.objects.filter(email=data_email).exists():
                #     return Response(data="User already exists.", status=status.HTTP_401_UNAUTHORIZED)
        message="You have been invited on Build EZI as %s by %s."%(Invite.objects.get(id=request.data.get('invite_id')).user_type,request.user.first_name)
        api_key = config('MJ_APIKEY_PUBLIC')
        api_secret = config('MJ_APIKEY_PRIVATE')
        mailjet = Client(auth=(api_key, api_secret), version='v3.1')
        data = {
        'Messages': [
                {
                    "From": {
                        "Email": "darren_bedford14@outlook.com",
                        "Name": "BUILD EZI"
                    },
                    "To": [
                        {
                            "Email": data_email,
                            "Name":Invite.objects.get(id=request.data.get('invite_id')).first_name 
                        }
                    ],
                    "TemplateID": 3726019,
                    "TemplateLanguage": True,
                    "Subject": "INVITATION From BUILD EZI",
                    "Variables": {
            "firstname": Invite.objects.get(id=request.data.get('invite_id')).first_name,
            "lastname": Invite.objects.get(id=request.data.get('invite_id')).last_name,
            "message": message,
            "link": request.data['invite_link']
        }
                }
            ]
        }
        result = mailjet.send.create(data=data)
        print (result.status_code)
        print (result.json())
        return Response(status=status.HTTP_200_OK,data="Invitation successfully sent.")
    
    # @action(methods=['POST'],detail=True,url_path='accept',url_name='accept_invite')
    # def accept(self, request, pk, *args, **kwargs):
    #     obj_invite=Invite.objects.get(invite_id=pk)
    #     user_serializer = RegistrationSerializer(data=request.data)
    #     user_serializer.is_valid(raise_exception=True)
    #     user_serializer.save()
    #     invite_serializer=InviteSerializer(instance=obj_invite)
    #     invite_serializer.update(instance=obj_invite, validated_data={'status':'accepted'})
    #     return Response(data=user_serializer.data,status=status.HTTP_201_CREATED)
    # @action(methods=['GET'],detail=True,url_path='reject',url_name='invite_rejected')
    # def reject(self,request,pk,*args,**kwargs):
    #     obj_invite=Invite.objects.get(invite_id=pk)
    #     invite_serializer=InviteSerializer(instance=obj_invite)
    #     invite_serializer.update(instance=obj_invite,validated_data={'status':'rejected'})
    #     return Response(data='Invitation Rejected.', status=status.HTTP_200_OK)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(
            self.get_queryset()).order_by('-invite_date')
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)  

#______________________Login_Viewset
class TokenAuthViewset(viewsets.GenericViewSet, mixins.CreateModelMixin):
    permission_classes = [AllowAny]
    serializer_class = LoginSerializer

    def create(self, request, *args, **kwargs):
        data = request.data
        user = None
        email_check= data.get('email').lower()
        try: 
            if data.get('username'):
                user = User.objects.get(username=data['username'])  
                if user.invite_message=="":
                    user = User.objects.get(email=email_check) 
                else:
                    return Response(data='User doesnot exist', status=status.HTTP_402_PAYMENT_REQUIRED) 
            elif email_check:
                user = User.objects.get(email=email_check) 
                if user.invite_message=="":
                    user = User.objects.get(email=email_check) 
                else:
                    return Response(data='User doesnot exist', status=status.HTTP_402_PAYMENT_REQUIRED)
            elif data.get('facebook_token'):
                user = User.objects.get(facebook_token=data['facebook_token'])
                serializer = self.serializer_class(instance=user)
                if user.message=='':
                    return Response(data=serializer.data, status=status.HTTP_200_OK)
                else:
                    return Response(data='User doesnot exist', status=status.HTTP_402_PAYMENT_REQUIRED)
            elif data.get('apple_token'):
                user = User.objects.get(apple_token=data['apple_token'])
                serializer = self.serializer_class(instance=user)
                if user.message=='':
                    return Response(data=serializer.data, status=status.HTTP_200_OK)
                else:
                    return Response(data='User doesnot exist', status=status.HTTP_402_PAYMENT_REQUIRED)
            elif data.get('google_token'):
                user = User.objects.get(google_token=data['google_token'])
                serializer = self.serializer_class(instance=user)
                if user.message=='':
                    return Response(data=serializer.data, status=status.HTTP_200_OK)
                else:
                    return Response(data='User doesnot exist', status=status.HTTP_402_PAYMENT_REQUIRED)
            else:
                raise exceptions.AuthenticationFailed(_('No valid auth credentials found.'))
            
            if not user.is_active:
                raise exceptions.AuthenticationFailed(
                    _('User inactive or deleted.'))

            if user.check_password(data.get('password')):
                serializer = self.serializer_class(instance=user)
                if user.message=='':
                    return Response(data=serializer.data, status=status.HTTP_200_OK)
                else:
                    return Response(data='User doesnot exist', status=status.HTTP_402_PAYMENT_REQUIRED)
            else:
                if user.message=='':
                    return Response (data='Invalid username/password.', status=status.HTTP_400_BAD_REQUEST)          
                else:
                    return Response(data='User doesnot exist', status=status.HTTP_402_PAYMENT_REQUIRED )
        except UserModel.DoesNotExist:
            if email_check:
                return Response(data='User doesnot exist', status=status.HTTP_402_PAYMENT_REQUIRED)
            else:
                raise exceptions.AuthenticationFailed(
                        _('Login Failed.'))

class OccupationViewset(viewsets.GenericViewSet, mixins.CreateModelMixin, mixins.ListModelMixin,mixins.RetrieveModelMixin):
    serializer_class = OccupationSerializer
    queryset = Occupation.objects.all()
    def get_permissions(self):
        if self.action == "create":
            return [AllowAny()]       
        return [AllowAny()]
        

def _unicode_ci_compare(s1, s2):
    """
    Perform case-insensitive comparison of two identifiers, using the
    recommended algorithm from Unicode Technical Report 36, section
    2.11.2(B)(2).
    """
    return unicodedata.normalize('NFKC', s1).casefold() == unicodedata.normalize('NFKC', s2).casefold()

class PasswordResetViewset(viewsets.GenericViewSet,mixins.CreateModelMixin, PasswordContextMixin):
    permission_classes=[AllowAny]
    serializer_class = LoginSerializer
    form_class = PasswordResetForm
    token_generator = default_token_generator
    from_email = None
    email_template_name = 'password_reset_email.html'
    subject_template_name = 'registration/password_reset_subject.txt'
    html_email_template_name = 'password_reset_email.html'
    extra_email_context = None   


    def get_users(self, email):
       
        """Given an email, return matching user(s) who should receive a reset.

        This allows subclasses to more easily customize the default policies
        that prevent inactive users and users with unusable passwords from
        resetting their password.
        """
        UserModel=get_user_model()
        email_field_name = UserModel.get_email_field_name()
        active_users = UserModel._default_manager.filter(**{
            '%s__iexact' % email_field_name: email,
            'is_active': True,
        })
        return (
            u for u in active_users
            if u.has_usable_password() and
            _unicode_ci_compare(email, getattr(u, email_field_name))
        )


    def save(self, domain_override=None,
            use_https=False, token_generator=default_token_generator, request=None,
            extra_email_context=None):
        """
        Generate a one-use only link for resetting password and send it to the
        user.
        """
        if request.query_params.get("email"):
            email = request.query_params.get("email")
        else:
            Response(data="Please specify an email", status=status.HTTP_400_BAD_REQUEST)
        if not domain_override:
            current_site = get_current_site(request)
            site_name = current_site.name
            domain = current_site.domain
        else:
            site_name = domain = domain_override
        email_field_name = UserModel.get_email_field_name()
        for user in self.get_users(email):
            user_email = getattr(user, email_field_name)
            context = {
                'email': user_email,
                'domain': domain,
                'site_name': site_name,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'user': user,
                'token': token_generator.make_token(user),
                'protocol': 'https' if use_https else 'http',
                **(extra_email_context or {}),
            }
        api_key = config('MJ_APIKEY_PUBLIC')
        api_secret = config('MJ_APIKEY_PRIVATE')
        mailjet = Client(auth=(api_key, api_secret), version='v3.1')
        resetlink= 'https' if use_https else 'http'+"://"+domain+"/"+"accounts/reset/"+urlsafe_base64_encode(force_bytes(user.pk))+"/"+token_generator.make_token(user)
        data = {
        'Messages': [
                {
                    "From": {
                        "Email": "darren_bedford14@outlook.com",
                        "Name": "BUILD EZI"
                    },
                    "To": [
                        {
                            "Email": request.query_params.get("email"),
                            "Name": ""
                        }
                    ],
                    "TemplateID": 3705814,
                    "TemplateLanguage": True,
                    "Subject": "Reset Password From BUILD EZI",
                    "Variables": {
                        "firstname": User.objects.get(email=request.query_params.get("email")).first_name ,
                        "lastname": User.objects.get(email=request.query_params.get("email")).last_name,
                        "link": resetlink
                    }
                }
            ]
        }
        result = mailjet.send.create(data=data)
        print (result.status_code)
        print (result.json())
        return Response(data="Password reset email sent",status=status.HTTP_200_OK,)
    def list(self, request, *args, **kwargs):
        """
        Handle POST requests: instantiate a form instance with the passed
        POST variables and then check if it's valid.
        """
        if not User.objects.filter(email=request.query_params.get("email")).exists() :
                return Response(data="User with this email doesn't exist",status=status.HTTP_400_BAD_REQUEST,)
        return self.save(request=request)

class ProfileDetailsViewset(viewsets.GenericViewSet,mixins.RetrieveModelMixin):
    permission_classes=[IsAuthenticated]
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return LoginSerializer
        if self.action=='update_profiledetails':
            return ProfileDetailsUpdateSerializer
    def get_queryset(self):
        if self.action=='update_profiledetails':
            return self.request.user

    def retrieve(self, request, *args, **kwargs):
        user=User.objects.get(pk=request.user.id)
        if  user.trial_ended==date.today() and user.is_subscription=="TRIAL":
            user.is_subscription="NO_ACTIVE_PLAN"
            user.save()
        instance=User.objects.get(pk=request.user.id)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(methods=['PUT'], detail=False, url_path='update', url_name='update_profiledetails')
    def update_profiledetails(self, request, *args, **kwargs):
        request.data._mutable=True
        instance=User.objects.get(pk=request.user.id)
        serializer=self.get_serializer(data=request.data)
        serializer=self.get_serializer(instance,data=request.data,partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.update(instance=instance,validated_data=(request.data))
        switch="UPDATEPROFILE"
        if instance.user_type=="worker":
            try:
                    payload_data={"EventType": instance.user_type,
                    "EventAction": "update",
                    "AppCustomerId": instance.id,
                    "WorkerId": instance.id,
                    "FirstName": instance.first_name,
                    "LastName": instance.last_name,
                    "Email": instance.email,
                    "Phone": instance.phone,
                    "SignUpDate": instance.created_date.date().strftime("%d/%m/%Y"),
                    "Company":instance.company,
                    "Occupation":instance.occupation.name
                    }
                    salesforce(switch,payload_data,request)
            except Exception as e:
                    print(e)
            return Response(serializer.data,status=status.HTTP_200_OK) 
        if instance.user_type=="builder":
            try:
                    payload_data={"EventType": instance.user_type,
                    "EventAction": "update",
                    "AppCustomerId": instance.id,
                    "BuilderId": instance.id,
                    "FirstName": instance.first_name,
                    "LastName": instance.last_name,
                    "Email": instance.email,
                    "Phone": instance.phone,
                    "SignUpDate": instance.created_date.date().strftime("%d/%m/%Y"),
                    "Company":instance.company,
                    "Occupation":instance.occupation.name
                    }
                    salesforce(switch,payload_data,request)
            except Exception as e:
                    print(e)
            return Response(serializer.data,status=status.HTTP_200_OK) 
        if instance.user_type=="worker":
            try:
                    payload_data={"EventType": instance.user_type,
                    "EventAction": "update",
                    "AppCustomerId": instance.id,
                    "ClientId": instance.id,
                    "FirstName": instance.first_name,
                    "LastName": instance.last_name,
                    "Email": instance.email,
                    "Phone": instance.phone,
                    "SignUpDate": instance.created_date.date().strftime("%d/%m/%Y"),
                    "Company":instance.company,
                    "Occupation":instance.occupation.name
                    }
                    salesforce(switch,payload_data,request)
            except Exception as e:
                    print(e)
            return Response(serializer.data,status=status.HTTP_200_OK) 

class ChangePasswordViewset(viewsets.GenericViewSet,mixins.UpdateModelMixin,mixins.CreateModelMixin):
    permission_classes=[IsAuthenticated]
    serializer_class=ChangePasswordSerializer
    def get_queryset(self):
        return self.request.user
    

    def create(self, request,*args, **kwargs):
        data=request.data
        instance=User.objects.get(pk=request.user.id)
        serializer=self.get_serializer(data=request.data)
        if request.user.check_password(data.get('old_password')):
                serializer = self.serializer_class(instance=request.user)
                serializer=self.get_serializer(instance,data=request.data,partial=True)
                serializer.is_valid(raise_exception=True)
                instance.set_password(request.data.get('new_password'))
                instance.save()
                headers = self.get_success_headers(serializer.data)
                return Response(data=serializer.data, status=status.HTTP_200_OK)
        return Response("Old password is incorrect ",status=status.HTTP_400_BAD_REQUEST)
       
class InductionQuestionsViewset(viewsets.GenericViewSet, mixins.CreateModelMixin, mixins.DestroyModelMixin,mixins.ListModelMixin,mixins.UpdateModelMixin):
    def get_permissions(self):
        if self.action == "create" :
            return [IsAuthenticated()]
        if self.action == "list":
            return [AllowAny()]
        return [AllowAny()]

    queryset = InductionQuestions.objects.all()

    def get_serializer_class(self):
        if self.action == 'create' or self.action == "list" or self.action=="update_induction_question":
            return InductionQuestionSerializer
    def create(self, request, *args, **kwargs):
        request.data['created_by']=request.user.id
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data,status=status.HTTP_200_OK,headers=headers)

    @action(methods=['POST'],detail=False,url_path='update',url_name='update_induction_question')
    def update_induction_question(self, request, *args, **kwargs):
        if request.query_params['question_id']:
            question=InductionQuestions.objects.get(pk=request.query_params['question_id'])
            if question.created_by==request.user:
                serializer=self.get_serializer(question,data=request.data,partial=True)
                serializer.is_valid(raise_exception=True)
                serializer.update(instance=question,validated_data=(request.data))
                headers = self.get_success_headers(serializer.data)
                return Response(serializer.data,status=status.HTTP_200_OK,headers=headers)
            else:
                return Response(data='You are Not Authorize to update this Induction_Question',status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(data='Question Id is missing.',status=status.HTTP_400_BAD_REQUEST)

    def list(self, request, *args, **kwargs):

        queryset =InductionQuestions.objects.all().order_by('id')
        # else:
        #     queryset = self.filter_queryset(
        #             self.get_queryset()).order_by('-created_date')
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class InductionAnswersViewset(viewsets.GenericViewSet, mixins.CreateModelMixin, mixins.ListModelMixin,mixins.UpdateModelMixin):
    def get_permissions(self):
        if self.action == "create" :
            return [IsAuthenticated()]
        if self.action == "list":
            return [IsAuthenticated()]

        return [AllowAny()]

    def get_queryset(self):
        if self.action == "delete" or self.action=="create":
            return self.request.user
        

    def get_serializer_class(self):
        if self.action == 'create' :
            return InductionAnswersSerializer
        if self.action == 'list':
            return InductionAnswersListSerializer

    def create(self, request, *args, **kwargs):
        user=request.user
        result=[]
        list_of_data=[]
        if self.request.user and request.data:
            for i in request.data:    
                # data = request.data
                i["answered_by"]=request.user.id
                serializer = self.get_serializer(data=i)
                serializer.is_valid(raise_exception=True)
                self.perform_create(serializer)
                result=InductionQuestions.objects.get(id=serializer.data.get('question'))
                data=serializer.data
                data['question']={"id":result.id,"question":result.question,"correct_answer":result.correct_answer}
                headers = self.get_success_headers(serializer.data)
                # return Response(data, status=status.HTTP_201_CREATED, headers=headers)
                list_of_data.append(data)
            return Response(data=list_of_data,status=status.HTTP_200_OK,headers=headers)
        else:
            return Response('Incomplete Data', status=status.HTTP_404_NOT_FOUND)    

    def list(self, request, *args, **kwargs):
        if request.query_params['user_id']:
            if self.filter_queryset(self.get_queryset())==None:
                queryset =InductionAnswers.objects.filter(answered_by=request.query_params['user_id'])
            # else:
            #     queryset = self.filter_queryset(
            #             self.get_queryset()).order_by('-created_date')
                page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)

            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)

# class ExportCSVUsersViewset(viewsets.GenericViewSet):
#     permission_classes = [IsAdminUser]
#     serializer_class = LoginSerializer
#     queryset = User.objects.all()
#     def get(self, request, *args, **kwargs):
#         response = HttpResponse(content_type='text/csv')
#         response['Content-Disposition'] = 'attachment; filename="export.csv"'
#         writer = csv.writer(response)
#         for user in User.objects.all().exclude(user_type='builder'):
#             row = ''.join([
#                 user.first_name,
#                 user.last_name,
#                 # assigned_courses.count(),
#                 # completed_courses.count()
#             ])
#             writer.writerow(row)
#         return response