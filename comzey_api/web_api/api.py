from datetime import datetime, timezone
import json
import unicodedata

from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404
import requests
from accounts.models import User
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth import authenticate
from .serializers import UserSerializer,UserListSerializer,ProjectSerializer, AdminUpdateProfileSerializer , AdminPasswordResetSerializer
from django.contrib.auth.models import auth 
from django.contrib.auth import get_user_model
from rest_framework import status,generics, mixins, viewsets
from django.contrib.auth.forms import PasswordResetForm, UserModel
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny,IsAdminUser
# from rest_framework.authentication import TokenAuthentication
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.hashers import check_password
from django.core import exceptions
from django.contrib.auth import authenticate, login
from rest_framework_jwt.views import ObtainJSONWebToken, jwt_response_payload_handler, VerifyJSONWebToken, refresh_jwt_token
from rest_framework_jwt.authentication import JSONWebTokenAuthentication
# from accounts.models import BlacklistedToken
from rest_framework_jwt.settings import api_settings
from django.db.models import Q
from api.models import Project
from api.serializers import ProjectDetailsSerializer
from rest_framework.decorators import api_view, permission_classes
from rest_framework_jwt.views import obtain_jwt_token, refresh_jwt_token, verify_jwt_token
from rest_framework.renderers import JSONRenderer
from django.core.mail import send_mail
from django.urls import reverse
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from comzey_api.renderer import CustomRenderer
from django.db import transaction
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from decouple import config
from mailjet_rest import Client
import base64
# from accounts.models import BlacklistedToken

# User = get_user_model()








class WebAuthAPIView(APIView):
    
    permission_classes = [AllowAny]
    serializer_class = UserSerializer
    authentication_classes = [JSONWebTokenAuthentication]
    renderer_classes = [JSONRenderer]

    def post(self, request):
        data = request.data
        user = None
        email_check = data.get('email').lower()

        try:
            user = User.objects.get(email=email_check, is_superuser=True)
            if not user.is_active:
                raise exceptions.AuthenticationFailed(
                    _('User inactive or deleted.'))

            if check_password(data.get('password'), user.password):
                # login(request, user)
                serializer = self.serializer_class(instance=user)
                jwt_token = serializer.get_jwt_token(user)
              
                return Response({
                    'status': 'success',
                    'code' : status.HTTP_200_OK,
                    'data' : {
                        
                        'jwt_token' : jwt_token,
                        'email' : user.email,
                        'username' : user.username,
                        'first_name' : user.first_name,
                        'last_name' : user.last_name,
                        'user_type' : user.user_type,
                        
                    },
                        'message' : '',
                
                })
            else:
                return Response ({'status' : 'error' , 'code':status.HTTP_400_BAD_REQUEST,'data' : {},'message' : 'Invalid email/password.'} )
        except UserModel.DoesNotExist:
            return Response({'status' : 'error' , 'code':status.HTTP_400_BAD_REQUEST,'data' : {},'message' : 'Invalid email/password.'})
        


class UserList(generics.ListAPIView):

    authentication_classes = [JSONWebTokenAuthentication]
    permission_classes = [IsAuthenticated, IsAdminUser]
    serializer_class = UserListSerializer
    renderer_classes = [JSONRenderer]

    

    def get_queryset(self):

        queryset = User.objects.filter(is_superuser=False)

        user_type = self.request.query_params.get('user_type', None)
        first_name = self.request.query_params.get('first_name', None)
        last_name = self.request.query_params.get('last_name', None)
        occupation = self.request.query_params.get('occupation', None)
        fullname = self.request.query_params.get('fullname')


        if user_type is not None:
            user_type = user_type.lower()
            queryset = queryset.filter(user_type__icontains=user_type)

        if first_name is not None:
            queryset = queryset.filter(Q(first_name__icontains=first_name) | Q(last_name__icontains=first_name))

        if last_name is not None:
            queryset = queryset.filter(Q(first_name__icontains=last_name) | Q(last_name__icontains=last_name))

        
        if occupation is not None:
            occupation = user_type.lower()
            queryset = queryset.filter(occupation__name__icontains=occupation)

        if fullname is not None:
            if len(fullname) == 1:
                letter = fullname.lower()
                queryset = queryset.filter(Q(first_name__istartswith=letter) | Q(last_name__istartswith=letter))
            if ' ' in fullname:
                names = fullname.split()
                if len(names) > 1:
                    first_name = names[0]
                    last_name = ' '.join(names[1:])
                    queryset = queryset.filter(Q(first_name__icontains=first_name) & Q(last_name__icontains=last_name))
            else:
                queryset = queryset.filter(Q(first_name__icontains=fullname) | Q(last_name__icontains=fullname))

        return queryset
    
    def get(self, request, *args, **kwargs):
        try:
            queryset = self.get_queryset()
            data = []
            for user in queryset:
                user_data = {
                    'id': user.id,
                    'firstName': user.first_name,
                    'lastName': user.last_name,
                    'email': user.email,
                    'type': user.user_type,
                    'image': user.profile_picture,
                    'occupation': {
                        'id': user.occupation.id,
                        'name': user.occupation.name,
                    },
                    'isActive': user.is_active,
                }
                data.append(user_data)
            response_data = {
            'status': 'success',
            'code': 200,
            'message': '',
            'data': data,
        }
            return Response(response_data)

        except Exception as e:
            return Response({'status' : 'error', 'code':status.HTTP_400_BAD_REQUEST,'data' : {},'message' : str(e)})
        


class UserDetailView(APIView):

    authentication_classes = [JSONWebTokenAuthentication]
    permission_classes = [IsAuthenticated, IsAdminUser]
    serializer_class = UserListSerializer
    renderer_classes = [JSONRenderer]

    def get(self, request):
        user_id = request.query_params.get('id')
        if user_id is None:
            return Response({'status': 'error','code' : status.HTTP_400_BAD_REQUEST,'data' : {},'message' : 'User id is not defined'}, )
        try:
            user = User.objects.get(id=user_id)
         
            return Response( {
                "status" : "success",
                "code" : status.HTTP_200_OK,
                'data':{
                    'id': user.id,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'email': user.email,
                    'phone' : "",
                    'user_type' : user.user_type,
                    'is_subscription' : user.is_subscription,
                    'trial_ended' : user.trial_ended,

                    "occupation": { 
                    "name": user.occupation.name, 
                    "id": user.occupation.id 

                    }, 
                    "company": "info", 
                    "signature": "", 
                    "username": "cee20d47-2efc-4482-b4f7-1993fd83aeb5", 
                    "profile_picture": "", 
                    "safety_card": "", 
                    "trade_licence": "" 
                
                },
                'message' : ""
               

                }, )
        except User.DoesNotExist:
            return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)


class ProjectList(generics.ListAPIView):
    authentication_classes = [JSONWebTokenAuthentication]
    permission_classes = [IsAuthenticated, IsAdminUser]
    serializer_class = ProjectSerializer
    renderer_classes = [JSONRenderer]
    queryset = Project.objects.all()
    

    def get_queryset(self):
        queryset = Project.objects.all()
        status = self.request.query_params.get('status', None)
        created_by = self.request.query_params.get('created_by', None)
        project_name = self.request.query_params.get('project_name', None)
        if status is not None:
            queryset = queryset.filter(status__icontains=status)
        if created_by is not None:
            queryset = queryset.filter(client__username__icontains=created_by)
        if project_name is not None:
           project_name = project_name.lower() 
           queryset = queryset.filter(name__icontains=project_name)
        return queryset
    
    def list(self, request, *args, **kwargs):
        try:
            queryset = self.filter_queryset(self.get_queryset())
            serializer = self.get_serializer(queryset, many=True)
            data = {
            "status": "success",
            "code": 200,
            "message": "",
            "data": [],
            }
            for project in serializer.data:
                data["data"].append({
                    "id": project["id"],
                    "name": project["name"],
                    "address": {
                        "id": project["address"]["id"],
                        "name": project["address"]["name"],
                        "longitude": project["address"]["longitude"],
                        "latitude": project["address"]["latitude"],
                    },
                    "client": {
                        "email": project["client"]["email"],
                        "first_name": project["client"]["first_name"],
                        "last_name": project["client"]["last_name"],
                        "user_type": project["client"]["user_type"],
                        "occupation": {
                            "id": project["client"]["occupation"]["id"],
                            "name": project["client"]["occupation"]["name"],
                        },
                        "jwt_token": project["client"]["jwt_token"],
                    },
                    "description": project["description"],
                    "scope_of_work": project["scope_of_work"],
                    "created_date": project["created_date"],
                    "last_updated": project["last_updated"],
                    "worker": project["worker"],
                    "status": project["status"],
                    "quotations": project["quotations"],
                    "builder": {
                        "email": project["builder"]["email"],
                        "first_name": project["builder"]["first_name"],
                        "last_name": project["builder"]["last_name"],
                        "user_type": project["builder"]["user_type"],
                        "profile_picture": "",
                        "occupation": {
                            "id": project["builder"]["occupation"]["id"],
                            "name": project["builder"]["occupation"]["name"],
                        },
                        "jwt_token": project["builder"]["jwt_token"],
                    },
                })
            return Response(data)
        except:
            return Response({'status' : 'error', 'code':status.HTTP_400_BAD_REQUEST,'data' : {},'message' : 'Something went wrong.'})




class ProjectUpdateStatus(APIView):
    authentication_classes = [JSONWebTokenAuthentication]
    permission_classes = [IsAuthenticated, IsAdminUser]
    renderer_classes = [JSONRenderer]

    def get_serializer(self, *args, **kwargs):
        return ProjectSerializer(*args, **kwargs)

    def put(self, request, *args, **kwargs):
        try:
            project_id = request.query_params.get('id', None)
            print(project_id)
            if project_id is None:
                return Response({'status': 'error', 'code': status.HTTP_400_BAD_REQUEST, 'data': {}, 'message': 'Project ID is missing.'})
            
            project = Project.objects.filter(id=project_id).first()
            if project is None:
                return Response({'status': 'error', 'code': status.HTTP_404_NOT_FOUND, 'data': {}, 'message': 'Project not found.'})
            
            new_status = request.query_params.get('status', None)
            if new_status is None:
                return Response({'status': 'error', 'code': status.HTTP_400_BAD_REQUEST, 'data': {}, 'message': 'Status is missing.'})
            
            project.status = new_status
            project.save()
            
            serializer = self.get_serializer(project)
            data = {
                "status": "success",
                "code": status.HTTP_200_OK,
                "message": "Project status updated successfully.",
                "data": serializer.data,
            }
            return Response(data)
        
        except Exception as e:
            return Response({'status' : 'error', 'code': status.HTTP_400_BAD_REQUEST, 'data' : {},'message' : str(e)})


    



class ProjectDetailView(APIView):

    authentication_classes = [JSONWebTokenAuthentication]
    permission_classes = [IsAuthenticated, IsAdminUser]
    serializer_class = ProjectSerializer
    renderer_classes = [JSONRenderer]

    def get(self, request):
        try:
            project_id = request.GET.get('id')
            try:
                project = Project.objects.get(id=project_id)
            except Project.DoesNotExist:
                return Response({"status": "failure", "code": status.HTTP_404_NOT_FOUND, "data": {}, "message": "Project not found"})
            serializer = ProjectDetailsSerializer(project)
            data = {
                "status": "success",
                "code": status.HTTP_200_OK,
                "data": serializer.data,
                "message": ""
            }
            return Response(data)
        except:
            return Response({'status' : 'error', 'code':status.HTTP_400_BAD_REQUEST,'data' : {},'message' : 'Something went wrong.'})
        




class UserDeleteAPIView(APIView):

    permission_classes = [AllowAny]
    renderer_classes = [JSONRenderer]
    def delete(self, request, pk):
        try:
            with transaction.atomic():
                user = User.objects.get(pk=pk)
                user.delete()
                data = {
                    "status": "success",
                    "code": status.HTTP_200_OK,
                    "data": {},
                    "message": ""
            }
            return Response(data)
        except User.DoesNotExist:
            return Response({'status' : 'error', 'code':status.HTTP_400_BAD_REQUEST,'data' : {},'message' : 'Something went wrong.'})





class DahsboardAPIView(APIView):

    authentication_classes = [JSONWebTokenAuthentication]
    permission_classes = [IsAuthenticated, IsAdminUser]
    renderer_classes = [CustomRenderer]
    def get(self, request):

        try:
            user_count = User.objects.count()
            projects_count = Project.objects.count()
            client_id = config('CLIENT_ID')
            client_secret = config('CLIENT_SECRET')

            url = "https://api.sandbox.paypal.com/v1/oauth2/token"
            data = {
                "client_id": client_id,
                "client_secret": client_secret,
                "grant_type": "client_credentials"
            }
            headers = {
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Authorization": "Basic {0}".format(base64.b64encode((client_id + ":" + client_secret).encode()).decode())
                }


            token = requests.post(url, data, headers=headers)
            access_token = token.json()
            print(access_token)

            url = "https://api.sandbox.paypal.com/v1/reporting/balances"

            headers = {
                "Content-Type": "application/json",
                "Authorization": "Bearer {0}".format(access_token)
            }

            r = requests.get(url, headers=headers, auth=(client_id, client_secret))
            result = r.json()
            
            print(result)
            total_balance = result["balances"][0]["available_balance"]["value"]
            data = {
                    "total_user" : user_count,
                    "total_projects" : projects_count,
                    "total_balance": total_balance
                }
            return Response(data)
        
        except Exception as e:
            return Response({'status' : 'error', 'code':status.HTTP_400_BAD_REQUEST,'data' : {},'message' : str(e)})




        
        
        
class AdminUpdateProfileView(APIView):

    authentication_classes = [JSONWebTokenAuthentication]
    permission_classes = [IsAuthenticated, IsAdminUser]
    renderer_classes = [CustomRenderer]
    def patch(self, request):
        print("here")
        try:
            if self.request.user:
                instance = User.objects.get(pk=request.user.id)
                serializer = AdminUpdateProfileSerializer(data=request.data, partial=True)
                serializer.is_valid(raise_exception=True)
                serializer.update(instance=instance,validated_data=(request.data))
                data = {
                    
                    "data" : serializer.data
                }
                return Response(data)
        except Exception as e:
            return Response({'status' : 'error', 'code':status.HTTP_400_BAD_REQUEST,'data' : {},'message' : str(e)})




class AdminChangePasswordView(APIView):

    authentication_classes = [JSONWebTokenAuthentication]
    permission_classes = [IsAuthenticated, IsAdminUser]
    renderer_classes = [CustomRenderer]
    def post(self,request,format=None):
        
        try:
            old_password = request.data.get('old_password')
            new_password = request.data.get('new_password')
            confirm_password = request.data.get('confirm_password')
            user = request.user
            if not user.check_password(old_password):
                return Response('Old password is incorrect', status=status.HTTP_400_BAD_REQUEST)
            if old_password == new_password:
                return Response('Old and new passwords cannot be the same', status=status.HTTP_400_BAD_REQUEST)
            if new_password != confirm_password:
                return Response('Password and confirm password do not match', status=status.HTTP_400_BAD_REQUEST)
            if len(new_password) < 8:
                return Response( 'Password should be at least 8 characters', status=status.HTTP_400_BAD_REQUEST)
            user.set_password(new_password)
            user.save()
            return Response({'data': 'Password changed successfully'})
        except Exception as e: 
          return Response({'status' : 'error', 'code':status.HTTP_400_BAD_REQUEST,'data' : {},'message' : str(e)})




class AdminPasswordResetView(APIView):
    
    serializer_class = AdminPasswordResetSerializer
    form_class = PasswordResetForm
    token_generator = default_token_generator
    from_email = config('EMAIL_HOST_USER')
    email_template_name = 'password_reset_email.html'
    subject_template_name = 'registration/password_reset_subject.txt'
    html_email_template_name = 'password_reset_email.html'
    extra_email_context = None
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        if not email:
            return Response({"error": "Please provide an email"}, status=status.HTTP_400_BAD_REQUEST)

        UserModel = get_user_model()
        email_field_name = UserModel.get_email_field_name()
        try:
            user = UserModel._default_manager.get(**{
                email_field_name: email,
                'is_staff': True,
            })
        except UserModel.DoesNotExist:
            return Response({"error": "Admin with provided email does not exist"}, status=status.HTTP_404_NOT_FOUND)

        if not user.is_active:
            return Response({"error": "Admin account is not active"}, status=status.HTTP_400_BAD_REQUEST)

        if not user.has_usable_password():
            return Response({"error": "Admin account has an unusable password"}, status=status.HTTP_400_BAD_REQUEST)

        domain = get_current_site(request).domain
        email_context = {
            'email': email,
            'domain': domain,
            'site_name': domain,
            'uid': urlsafe_base64_encode(force_bytes(user.pk)),
            'user': user,
            'token': self.token_generator.make_token(user),
            'protocol': 'https' if request.is_secure() else 'http',
            **(self.extra_email_context or {}),
        }

        resetlink = self.request.build_absolute_uri(
            reverse(
                'password_reset_confirm',
                kwargs={
                    'uidb64': email_context['uid'],
                    'token': email_context['token'],
                },
            )
        )

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
                            "Email": email,
                            "Name": ""
                        }
                    ],
                    "TemplateID": 3705814,
                    "TemplateLanguage": True,
                    "Subject": "Reset Password From BUILD EZI",
                    "Variables": {
                        "firstname": user.first_name ,
                        "lastname": user.last_name,
                        "link": resetlink
                    }
                }
            ]
        }
        result = mailjet.send.create(data=data)
        print(result.status_code)
        print(result.json())
        return Response({"detail": "Password reset email sent"}, status=status.HTTP_200_OK)


          