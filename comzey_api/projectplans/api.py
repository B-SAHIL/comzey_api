from django.shortcuts import render
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from accounts.models import User
from api.models import Project,ProjectWorker
from projectnotifications.serializers import FCMSerializer
from rest_framework import mixins, viewsets
from comzey_api.custom_permissions import IsClient, IsBuilder, IsWorker
from comzey_api.notifications import  send_notification_thread
from projectplans.models import Plan
from projectplans.serializers import PlanSerializer
from projectnotifications.models import FcmNotifications

# includes ---------------->>>>>>>>>>>>>PlanViewSet
class PlanViewset(viewsets.GenericViewSet, mixins.CreateModelMixin, mixins.ListModelMixin):
    def get_permissions(self):
        if self.action == "create":
            return [IsBuilder(), IsClient()]
        if self.action == "list":
            return [IsAuthenticated()]
        return [AllowAny()]

    def get_queryset(self):
        if self.request.user.user_type=="builder":
            return Plan.objects.filter(project__builder=self.request.user)
        if self.request.user.user_type=="client":
            return Plan.objects.filter(project__client=self.request.user)
        if self.request.user.user_type=="worker":
            return Plan.objects.filter(project__worker=self.request.user)

    def get_serializer_class(self):
        if self.action == 'create' or self.action=='update_plan':
            return PlanSerializer
        if self.action == 'list':
            return PlanSerializer

    def create(self, request, *args, **kwargs):
        # request.data._mutable=True
        request.data["created_by"]=request.user.id
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        workers=ProjectWorker.objects.filter(project_id=request.data['project'])
        workers=[x.worker.id for x in workers]
        client=Project.objects.get(pk=request.data['project']).client.id
        receivers=workers+[client]
        for i in receivers:
            try:
                        notification_data={'title':'New Plan Created',
                        'sender_id':request.user.id,
                        'receiver_id':i,
                        'notification_type':"new_plan_created",
                        'plan':serializer.data.get('id'),
                        "project":request.data['project'],
                        'message':"A new plan has been created for %s project by %s %s"%(Project.objects.get(pk=request.data['project']).name,request.user.first_name,request.user.last_name)}  
                        notification=FCMSerializer(data=notification_data)
                        notification.is_valid(raise_exception=True)
                        notification.save()
                        data_object= {

                                "title": "New Plan Created",

                                "message": "A new plan has been created for %s project by %s %s"%(Project.objects.get(pk=request.data['project']).name,request.user.first_name,request.user.last_name),

                                "notification_type":"new_plan_created",

                                "project_id":request.data['project'],

                                'receiver_id':i,

                                "plan_id":serializer.data.get('id'),

                                "sender_id":request.user.id,

                                "fromNotification":True,

                            

                        }
                        send_notification_thread(User.objects.get(pk=notification_data.get("receiver_id")),data_object.get("title"),data_object.get("message"),data_object,len(FcmNotifications.objects.filter(receiver_id=notification_data.get("receiver_id"),watch="false")),request)
                        
            except Exception as e:
                print(e)
                return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(
            self.get_queryset()).order_by('-created_date')
        if request.query_params.get('project_id'):
            queryset = queryset.filter(
                project=request.query_params['project_id'])
        else:
            return Response(data='Please Specify project_id', status=status.HTTP_400_BAD_REQUEST)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(methods=['delete'], detail=True, url_path="")
    def delete(self, request, *args, **kwargs):
        if request.query_params.get('plan_id'):
            project=Plan.objects.get(id=request.query_params.get('plan_id')).project
            if self.request.user==Plan.objects.get(pk=request.query_params.get('plan_id')).created_by or self.request.user==Project.objects.get(id=project.id).builder or  self.request.user==Project.objects.get(id=project.id).client:
                workers=ProjectWorker.objects.filter(project_id=project.id)
                workers=[x.worker.id for x in workers]
                client=Project.objects.get(pk=project.id).client.id
                receivers=workers+[client]
                for i in receivers:
                    try:
                                notification_data={'title':'Plan Deleted',
                                'sender_id':request.user.id,
                                'receiver_id':i,
                                'notification_type':"plan_deleted",
                                "project":project.id,
                                'message':"Plan %s has been deleted for %s project by %s %s"%(Plan.objects.get(id=request.query_params.get('plan_id')).name,Project.objects.get(pk=project.id).name,request.user.first_name,request.user.last_name)}  
                                notification=FCMSerializer(data=notification_data)
                                notification.is_valid(raise_exception=True)
                                notification.save()
                                data_object= {

                                        "title": "Plan Deleted",

                                        "message": "Plan %s has been deleted for %s project by %s %s"%(Plan.objects.get(id=request.query_params.get('plan_id')).name,Project.objects.get(pk=project.id).name,request.user.first_name,request.user.last_name),

                                        "notification_type":"plan_deleted",

                                        "project_id":project.id,

                                        'receiver_id':i,

                                        "sender_id":request.user.id,

                                        "fromNotification":True

                                

                                }
                                send_notification_thread(User.objects.get(pk=notification_data.get("receiver_id")),data_object.get("title"),data_object.get("message"),data_object,len(FcmNotifications.objects.filter(receiver_id=notification_data.get("receiver_id"),watch="false")),request)
                                
                    except Exception as e:
                        print(e)
                instance = Plan.objects.get(pk=request.query_params.get('plan_id')).delete()
                return Response(data="Plan  Deleted Successfully", status=status.HTTP_200_OK)
            else: 
                return Response('You dont have the access to delete this Plan.', status=status.HTTP_404_NOT_FOUND)
        return Response('Please specify a Plan ID.', status=status.HTTP_404_NOT_FOUND)

    @action(methods=['PUT'],detail=False,url_path='update',url_name='update_plan')
    def update_plan(self, request,*args, **kwargs):
        if request.query_params.get('plan_id'):
            try:
                instance = self.get_queryset().get(
                    pk=request.query_params['plan_id'])
            except:
                return Response('Not found.', status=status.HTTP_404_NOT_FOUND)
        else:
            return Response('Please specify a plan_id.', status=status.HTTP_404_NOT_FOUND)
        obj_instance=Plan.objects.get(pk=request.query_params['plan_id'])
        serializer = PlanSerializer(instance=obj_instance, data=request.data, partial=True)
        serializer=self.get_serializer(instance,data=request.data,partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.update(instance=instance,validated_data=(request.data))
        headers = self.get_success_headers(serializer.data)
        obj_instance=Plan.objects.get(pk=request.query_params['plan_id'])
        obj_instance.worker_watch="false"
        obj_instance.save()
        obj_instance=Plan.objects.get(pk=request.query_params['plan_id'])
        obj_instance.client_watch="false"
        obj_instance.save()
        project=Plan.objects.get(id=request.query_params.get('plan_id')).project
        workers=ProjectWorker.objects.filter(project_id=project.id)
        workers=[x.worker.id for x in workers]
        client=Project.objects.get(pk=project.id).client.id
        receivers=workers+[client]
        for i in receivers:
            try:
                notification_data={'title':'Plan Updated',
                'sender_id':request.user.id,
                'receiver_id':i,
                'notification_type':"plan_updated",
                'plan':request.query_params.get('plan_id'),
                "project":project.id,
                "message": "Plan %s has been updated for %s project by %s %s"%(Plan.objects.get(id=request.query_params.get('plan_id')).name,Project.objects.get(pk=project.id).name,request.user.first_name,request.user.last_name)}
                notification=FCMSerializer(data=notification_data)
                notification.is_valid(raise_exception=True)
                notification.save()
                data_object= {

                        "title": "Plan Updated",

                        "message": "Plan %s has been updated for %s project by %s %s"%(Plan.objects.get(id=request.query_params.get('plan_id')).name,Project.objects.get(pk=project.id).name,request.user.first_name,request.user.last_name),

                        "notification_type":"plan_updated",

                        "project_id":project.id,

                        'receiver_id':i,

                        "plan_id":serializer.data.get('id'),

                        "sender_id":request.user.id,

                        "fromNotification":True

                

                }
                send_notification_thread(User.objects.get(pk=notification_data.get("receiver_id")),data_object.get("title"),data_object.get("message"),data_object,len(FcmNotifications.objects.filter(receiver_id=notification_data.get("receiver_id"),watch="false")),request)
                    
            except Exception as e:
                print(e)
                return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
 