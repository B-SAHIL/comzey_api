from django.shortcuts import render
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
import datetime
from comzey_api.notifications import  send_notification_thread
from accounts.models import User
from api.models import Project
from projectnotifications.serializers import FCMListSerializer, FCMSerializer
from comzey_api.custom_permissions import  IsBuilder
from rest_framework import mixins, viewsets
from projecttasks.models import Task
from projecttasks.serializers import TaskSerializer, TasksListSerializer, ScheduleWorkerSerializer
from projectnotifications.models import FcmNotifications
# includes ---------------->>>>>>>>>>>>>TaskViewset
class TaskViewset(viewsets.GenericViewSet, mixins.CreateModelMixin, mixins.RetrieveModelMixin):
    def get_permissions(self):
        if self.action == "create"or self.action=="task_verified":
            return [IsBuilder()]
        if self.action == "retrieve_task":
            return [IsAuthenticated()]
        return [IsAuthenticated()]

    def get_queryset(self):

        if self.action=="retrieve_task" :
            if self.request.user.user_type=='client':
                return Task.objects.filter(project__client=self.request.user)   
            if self.request.user.user_type=='builder':
                return Task.objects.filter(project__builder=self.request.user) 
            if self.request.user.user_type=='worker':
                return Task.objects.filter(project__worker=self.request.user)
        if self.action=="schedule":
            if self.request.user.user_type=='client':
                return Task.objects.filter(project__client=self.request.user,worker_action='accepted')   
            if self.request.user.user_type=='builder':
                return Task.objects.filter(project__builder=self.request.user,worker_action='accepted') 
            if self.request.user.user_type=='worker':
                # return Task.objects.filter(project__worker=self.request.user,worker_action='accepted') 
                return Task.objects.filter(assigned_worker=self.request.user,worker_action='accepted') 
                
        if self.request.user.user_type=='client':
            return Task.objects.filter(project__client=self.request.user)   
        if self.request.user.user_type=='builder':
            return Task.objects.filter(project__builder=self.request.user) 
        if self.request.user.user_type=='worker':
            return Task.objects.filter(assigned_worker=self.request.user)

    def get_serializer_class(self):
        if self.action == 'create':
            return TaskSerializer
        if self.action == 'retrieve_task' :
            return TaskSerializer
        if self.action=="schedule":
            if self.request.user.user_type=='client' or self.request.user.user_type=='builder':
                return TaskSerializer
            else:
                return ScheduleWorkerSerializer
        

    def create(self, request, *args, **kwargs):
        worker = User.objects.get(pk=request.data['assigned_worker'])
        if worker.user_type == 'worker':
            if worker in Project.objects.get(pk=request.data['project']).worker.all():
                try:
                    request.data['start_date'] = datetime.datetime.fromtimestamp(
                        int(request.data.get('start_date')))
                    request.data['end_date'] = datetime.datetime.fromtimestamp(
                        int(request.data.get('end_date')))
                except:
                    request.data['start_date'] = datetime.datetime.fromtimestamp(
                        int(request.data.get('start_date'))/1000)
                    request.data['end_date'] = datetime.datetime.fromtimestamp(
                        int(request.data.get('end_date'))/1000)
                request.data['start_date'] = request.data['start_date'].date()
                request.data['end_date'] = request.data['end_date'].date()
                serializer = self.get_serializer(data=request.data)
                serializer.is_valid(raise_exception=True)
                self.perform_create(serializer)
                headers = self.get_success_headers(serializer.data)
                try:
                    notification_data={'title':'Task Assigned',
                    'sender_id':request.user.id,
                    'receiver_id':User.objects.get(pk=request.data['assigned_worker']).id,
                    'notification_type':"task_assigned_worker",
                    'project':Project.objects.get(pk=request.data['project']).id,
                    'task':serializer.data.get('id'),
                    'message':"A new task has been assigned to you for %s project"%(Project.objects.get(pk=request.data['project']).name)}  
                    notification=FCMSerializer(data=notification_data)
                    notification.is_valid(raise_exception=True)
                    notification.save()
                    data_object= {

                            "title": "Task Assigned",

                            "message": "A new task has been assigned to you for %s project"%(Project.objects.get(pk=request.data['project']).name),

                            "notification_type":"task_assigned_worker",

                            "project_id":Project.objects.get(pk=request.data['project']).id,

                            'receiver_id':User.objects.get(pk=request.data['assigned_worker']).id,

                            "task_id":serializer.data.get('id'),

                            "sender_id":request.user.id,

                            "fromNotification":True

                    

                    }
                    send_notification_thread(User.objects.get(pk=notification_data.get("receiver_id")),data_object.get("title"),data_object.get("message"),data_object,len(FcmNotifications.objects.filter(receiver_id=notification_data.get("receiver_id"),watch="false")),request)
                    return Response(serializer.data, status=status.HTTP_200_OK)
                except Exception as e:
                    print(e)
                return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
            else:
                return Response('This worker is not assigned to this project.', status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response('Task can only be assigned to workers.', status=status.HTTP_400_BAD_REQUEST)
    
    @action(methods=['GET'],detail=False,url_path='accept',url_name='accept_task')
    def accept(self, request, *args, **kwargs):
        q = request.query_params
        if not q.get('task_id') :
            return Response(data='Invalid/Incomplete data', status=status.HTTP_400_BAD_REQUEST)
        obj = Task.objects.get(pk=q.get('task_id'),assigned_worker=request.user)
        obj.worker_action = 'accepted'
        obj.save()
        obj2=Task.objects.get(pk=q.get('task_id'))
        obj2.builder_watch='false'
        obj2.save()
        obj2=Task.objects.get(pk=q.get('task_id'))
        obj2.builder_watch_schedule="false"
        obj2.save()
        obj2=Task.objects.get(pk=q.get('task_id'))
        obj2.client_watch_schedule="false"
        obj2.save()

        try:
                    notification_data={'title':'Task Accepted',
                    'sender_id':request.user.id,
                    'receiver_id':Task.objects.get(pk=q.get('task_id')).project.builder.id,
                    'notification_type':"task_accepted",
                    'project':Task.objects.get(pk=q.get('task_id')).project.id,
                    'task':Task.objects.get(pk=q.get('task_id')).id,
                    'message':"Task has been accepted by worker %s %s for %s project."%(request.user.first_name,request.user.last_name,Task.objects.get(pk=q.get('task_id')).project.name)}  
                    notification=FCMSerializer(data=notification_data)
                    notification.is_valid(raise_exception=True)
                    notification.save()
                    data_object= {

                            "title": "Task Accepted",

                            "message": "Task has been accepted by worker %s %s for %s project."%(request.user.first_name,request.user.last_name,Task.objects.get(pk=q.get('task_id')).project.name),

                            "notification_type":"task_accepted",

                            "project_id":Task.objects.get(pk=q.get('task_id')).project.id,

                            'receiver_id':Task.objects.get(pk=q.get('task_id')).project.builder.id,

                            "task_id":Task.objects.get(pk=q.get('task_id')).id,

                            "sender_id":request.user.id,

                            "fromNotification":True

                    

                    }
                    send_notification_thread(User.objects.get(pk=notification_data.get("receiver_id")),data_object.get("title"),data_object.get("message"),data_object,len(FcmNotifications.objects.filter(receiver_id=notification_data.get("receiver_id"),watch="false")),request)
                    return Response(data='Task Accepted.', status=status.HTTP_200_OK)
        except Exception as e:
                print(e)
                return Response(data='Task Accepted.', status=status.HTTP_200_OK)
    
    @action(methods=['GET'],detail=False,url_path='completed',url_name='task_completed')
    def task_completed(self, request, *args, **kwargs):
        q = request.query_params
        if not q.get('task_id') :
            return Response(data='Invalid/Incomplete data', status=status.HTTP_400_BAD_REQUEST)
        if Task.objects.get(pk=q.get('task_id'),assigned_worker=request.user).worker_action=='accepted':
            obj = Task.objects.get(pk=q.get('task_id'),assigned_worker=request.user)
            obj.complete_status = 'completed'
            obj.save()
            obj2=Task.objects.get(pk=q.get('task_id'))
            obj2.builder_watch='false'
            obj2.save()
            obj2=Task.objects.get(pk=q.get('task_id'))
            obj2.builder_watch_schedule="false"
            obj2.save()
            obj2=Task.objects.get(pk=q.get('task_id'))
            obj2.client_watch_schedule="false"
            obj2.save()


            try:
                        notification_data={'title':'Task Mark Completed',
                        'sender_id':request.user.id,
                        'receiver_id':Task.objects.get(pk=q.get('task_id')).project.builder.id,
                        'notification_type':"task_mark_completed",
                        'project':Task.objects.get(pk=q.get('task_id')).project.id,
                        'task':Task.objects.get(pk=q.get('task_id')).id,
                        'message':"Task %s  has been mark completed by worker %s %s for project %s.Please verify task"%(Task.objects.get(pk=q.get('task_id')).task_name,request.user.first_name,request.user.last_name,Task.objects.get(pk=q.get('task_id')).project.name)}  
                        notification=FCMSerializer(data=notification_data)
                        notification.is_valid(raise_exception=True)
                        notification.save()
                        data_object= {

                                "title": "Task Mark Completed",

                                "message": "Task %s  has been mark completed by worker %s %s for project %s.Please verify task"%(Task.objects.get(pk=q.get('task_id')).task_name,request.user.first_name,request.user.last_name,Task.objects.get(pk=q.get('task_id')).project.name),

                                "notification_type":"task_mark_completed",

                                "project_id":Task.objects.get(pk=q.get('task_id')).project.id,

                                'receiver_id':Task.objects.get(pk=q.get('task_id')).project.builder.id,

                                "task_id":Task.objects.get(pk=q.get('task_id')).id,

                                "sender_id":request.user.id,

                                "fromNotification":True

                        

                        }
                        send_notification_thread(User.objects.get(pk=notification_data.get("receiver_id")),data_object.get("title"),data_object.get("message"),data_object,len(FcmNotifications.objects.filter(receiver_id=notification_data.get("receiver_id"),watch="false")),request)
                        return Response(data='Task Mark Completed.', status=status.HTTP_200_OK)
            except Exception as e:
                    print(e)
                    return Response(data='Task Mark Completed.', status=status.HTTP_200_OK)
        else:
            return Response(data='Task is not accepted by the worker.', status=status.HTTP_400_BAD_REQUEST)
    @action(methods=['GET'],detail=False,url_path='verified',url_name='task_verified')
    def task_verified(self, request, *args, **kwargs):
        q = request.query_params
        if not q.get('task_id') :
            return Response(data='Invalid/Incomplete data', status=status.HTTP_400_BAD_REQUEST)
        if Task.objects.get(pk=q.get('task_id')).complete_status=='completed':
            Task.objects.get(pk=q.get('task_id')).delete()
            try:
                        notification_data={'title':'Task Verified',
                        'sender_id':request.user.id,
                        'receiver_id':Task.objects.get(pk=q.get('task_id')).assigned_worker.id,
                        'notification_type':"task_verified",
                        'message':"Task %s  work has been Verified by Builder %s %s for project %s"%(Task.objects.get(pk=q.get('task_id')).task_name,request.user.first_name,request.user.last_name,Task.objects.get(pk=q.get('task_id')).project.name)}  
                        notification=FCMSerializer(data=notification_data)
                        notification.is_valid(raise_exception=True)
                        notification.save()
                        data_object= {

                                "title": "Task Verified",

                                "message": "Task %s work has been Verified by Builder %s %s for project %s"%(Task.objects.get(pk=q.get('task_id')).task_name,request.user.first_name,request.user.last_name,Task.objects.get(pk=q.get('task_id')).project.name),

                                "notification_type":"task_verified",

                                'receiver_id':Task.objects.get(pk=q.get('task_id')).assigned_worker.id,

                                "sender_id":request.user.id,

                                "fromNotification":True

                        

                        }
                        send_notification_thread(User.objects.get(pk=notification_data.get("receiver_id")),data_object.get("title"),data_object.get("message"),data_object,len(FcmNotifications.objects.filter(receiver_id=notification_data.get("receiver_id"),watch="false")),request)
                        return Response(data='Task Verified.', status=status.HTTP_200_OK)
            except Exception as e:
                    print(e)
                    return Response(data='Task Verified.', status=status.HTTP_200_OK)


    @action(methods=['GET'],detail=False,url_path='reject',url_name='reject_task')
    def reject(self,request,*args,**kwargs):
        q = request.query_params
        if not q.get('task_id') :
            return Response(data='Invalid/Incomplete data', status=status.HTTP_400_BAD_REQUEST)
        obj = Task.objects.get(pk=q.get('task_id'),assigned_worker=request.user)
        obj.worker_action = 'rejected'
        obj.save()
        obj2=Task.objects.get(pk=q.get('task_id'))
        obj2.builder_watch='false'
        obj2.save()
        try:
                    notification_data={'title':'Task Rejected',
                    'sender_id':request.user.id,
                    'receiver_id':Task.objects.get(pk=q.get('task_id')).project.builder.id,
                    'notification_type':"task_rejected",
                    'project':Task.objects.get(pk=q.get('task_id')).project.id,
                    'task':Task.objects.get(pk=q.get('task_id')).id,
                    'message':"Task has been rejected by worker %s %s for %s project."%(request.user.first_name,request.user.last_name,Task.objects.get(pk=q.get('task_id')).project.name)}  
                    notification=FCMSerializer(data=notification_data)
                    notification.is_valid(raise_exception=True)
                    notification.save()
                    data_object= {

                            "title": "Task Rejected",

                            "message": "Task has been rejected by worker %s %s for %s project."%(request.user.first_name,request.user.last_name,Task.objects.get(pk=q.get('task_id')).project.name),

                            "notification_type":"task_rejected",

                            "project_id":Task.objects.get(pk=q.get('task_id')).project.id,

                            'receiver_id':Task.objects.get(pk=q.get('task_id')).project.builder.id,

                            "task_id":Task.objects.get(pk=q.get('task_id')).id,

                            "sender_id":request.user.id,

                            "fromNotification":True

                    

                    }
                    send_notification_thread(User.objects.get(pk=notification_data.get("receiver_id")),data_object.get("title"),data_object.get("message"),data_object,len(FcmNotifications.objects.filter(receiver_id=notification_data.get("receiver_id"),watch="false")),request)
                    return Response(data='Task Rejected.', status=status.HTTP_200_OK)
        except Exception as e:
                print(e)
                return Response(data='Task Rejected.', status=status.HTTP_200_OK)

    @action(methods=['GET'], detail=False, url_path='retrieve', url_name='retrieve_task')
    def retrieve_task(self, request, *args, **kwargs):
        if request.query_params.get('task_id'):
            try:
                instance = self.get_queryset().get(
                    pk=request.query_params['task_id'])
            except:
                return Response('Not found.', status=status.HTTP_404_NOT_FOUND)
        else:
            return Response('Please specify a task ID.', status=status.HTTP_404_NOT_FOUND)
        # instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


    @action(methods=['GET'], detail=False, url_path='schedule', url_name='schedule')
    def schedule(self, request, *args, **kwargs):
        if request.query_params.get('project_id'):
            queryset = self.filter_queryset(
                self.get_queryset()).order_by('-id')
            queryset = queryset.filter(
                    project=request.query_params['project_id'])
            # if request.query_params.get('project_id'):
            #     queryset = queryset.filter(
            #         project=request.query_params['project_id'])
            # else:
            #     return Response(data='Please Specify project_id', status=status.HTTP_400_BAD_REQUEST)

            if request.query_params.get('date'):
                queryset = queryset.filter(
                start_date__lte=self.request.query_params.get('date'),end_date__gte=self.request.query_params.get('date'))
                page = self.paginate_queryset(queryset)
                if page is not None:
                    serializer = self.get_serializer(page, many=True)
                    result={"no_of_events":len(serializer.data),
                    "date":request.query_params.get('date'),
                    "month":"",
                    "schedule":serializer.data}
                    return self.get_paginated_response(result)

                serializer = self.get_serializer(queryset, many=True)
                result={"no_of_events":len(serializer.data),
                    "date":request.query_params.get('date'),
                    "month":"",
                    "schedule":serializer.data}
                return Response(result)
            elif request.query_params.get('month'):
                queryset = queryset.filter(
                start_date__month=self.request.query_params.get('month'))
                page = self.paginate_queryset(queryset)
                if page is not None:
                    serializer = self.get_serializer(page, many=True)
                    result={"no_of_events":len(serializer.data),
                    "date":"",
                    "month":request.query_params.get('month'),
                    "schedule":serializer.data}
                    return self.get_paginated_response(result)

                serializer = self.get_serializer(queryset, many=True)
                result={"no_of_events":len(serializer.data),
                    "date":"",
                    "month":request.query_params.get('month'),
                    "schedule":serializer.data}
                return Response(result)
            else:
                queryset = self.filter_queryset(
                self.get_queryset())
                queryset = queryset.filter(
                    project=request.query_params['project_id'])
                page = self.paginate_queryset(queryset)
                if page is not None:
                    serializer = self.get_serializer(page, many=True)
                    result={"no_of_events":len(serializer.data),
                    "date":"",
                    "month":"",
                    "schedule":serializer.data}
                    return self.get_paginated_response(result)

                serializer = self.get_serializer(queryset, many=True)
                result={"no_of_events":len(serializer.data),
                    "date":"",
                    "month":"",
                    "schedule":serializer.data}
                return Response(result)
        else:
                return Response(data='Please Specify project_id', status=status.HTTP_400_BAD_REQUEST)
