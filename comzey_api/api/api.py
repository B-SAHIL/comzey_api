from rest_framework import filters
from django.db.models.query import QuerySet
from rest_framework import mixins, viewsets
from accounts.serializers import LoginSerializer
from api.models import Project, ProjectWorker
from api.serializers import AllProjectUsersListSerializer, ClientListSerializer, CreateProjectSerializer,  ListProjectSerializer,  ProjectWorkerSerializer,  ProjectDetailsSerializer,    WorkerListSerializer
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from accounts.models import User
from datetime import date
from comzey_api.count import client_count, builder_count, worker_count
from comzey_api.custom_permissions import IsClient, IsBuilder, IsWorker
from comzey_api.notifications import  send_notification_thread
from projectdocuments.models import EOT, ROI, CheckListPunchList, Document, EOTReceiver, Files, IncidentReport, PunchList, PunchListReceiver, ROIReceiver, Safety, SiteRiskAssessment, ToolBox, ToolBoxReceiver, VariationReceiver, Variations
from projectnotifications.serializers import FCMSerializer
from projectplans.models import Plan
from projecttasks.models import Task
from projectdailylogs.models import DailyLog
from projecttasks.serializers import TasksListSerializer
from projectnotifications.models import FcmNotifications

#includes ----------------->>>>>>>>>> ProjectViewset, ClientViewSet
class ProjectViewset(viewsets.GenericViewSet, mixins.DestroyModelMixin ,mixins.CreateModelMixin, mixins.ListModelMixin):

    def get_permissions(self):
        if self.action == "create":
            return [IsBuilder()]
        if self.action == "archive_list":
             return [IsAuthenticated()]
        if self.action == "leave_job" :
            return [IsWorker()]
        if self.action=="leave_project_list":
            return [IsWorker()]
        if self.action == "archive_job":
            return [IsBuilder(),IsWorker()]
        if self.action == "get_tasks":
            return [IsAuthenticated()]
        if self.action == "delete":
            return [IsBuilder()]
        if self.action == "list" :
            return [IsAuthenticated()]  
        if self.action == "retrieve_project" or self.action=='projectusers':
            return [IsAuthenticated()]
        return [AllowAny()]

    def get_queryset(self):
        if self.action == "assigned_workers":
            return Project.objects.get(pk=self.kwargs['pk']).worker.all()
        if self.action == "unassigned_workers":
            # return User.objects.exclude(id__in=[i.id for i in Project.objects.get(pk=self.kwargs['pk']).worker.all()]).filter(user_type='worker')
            return User.objects.exclude(id__in=[i.id for i in Project.objects.get(pk=self.kwargs['pk']).worker.all()]).filter(user_type='worker').filter(invite_id__invited_by=self.request.user.id)
        if self.action == "list"or self.action=="count":
            if self.request.user.user_type=='worker':
                return Project.objects.filter(worker=self.request.user) 
            if self.request.user.user_type=='client':
                return Project.objects.filter(client=self.request.user)     
            if self.request.user.user_type=='builder':
                return Project.objects.filter(builder=self.request.user) 
        if self.action == "archive_list":    
            if self.request.user.user_type=='builder':
                return Project.objects.filter(builder=self.request.user).exclude(status='archive')
            if self.request.user.user_type=='client':
                return Project.objects.filter(client=self.request.user).exclude(status='archive')   
            if self.request.user.user_type=='worker':
                return Project.objects.filter(worker=self.request.user).exclude(status='archive')
        if self.action == "delete_list":    
            if self.request.user.user_type=='builder':
                return Project.objects.filter(builder=self.request.user).filter(status='archive')
        if self.action == "delete_project":    
            if self.request.user.user_type=='builder':
                return Project.objects.filter(builder=self.request.user)
        if self.action=="retrieve_project" or self.action=='projectusers':
            if self.request.user.user_type=='client':
                return Project.objects.filter(client=self.request.user)     
            if self.request.user.user_type=='builder':
                return Project.objects.filter(builder=self.request.user) 
            if self.request.user.user_type=='worker':
                return Project.objects.filter(worker=self.request.user) 

        return Project.objects.filter(builder=self.request.user)      
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']

    def get_serializer_class(self):
        if self.action == 'create':
            return CreateProjectSerializer
        if self.action == 'list' or self.action== 'archive_list' or self.action== 'delete_list':
            return ListProjectSerializer
        if self.action == 'retrieve_project':
            return ProjectDetailsSerializer
        if self.action == "unassigned_workers" or self.action == "assigned_workers":
            return WorkerListSerializer
        if self.action=="leave_project_list":
            return ProjectWorkerSerializer
        if self.action=="projectusers":
            return AllProjectUsersListSerializer

    def create(self, request, *args, **kwargs):
        client=User.objects.get(pk=request.data['client'])
        if client.user_type=='client':
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            try:
                notification_data={'title':'New Project Added',
                'sender_id':request.user.id,
                'receiver_id':client.id,
                'notification_type':"project_assigned_client",
                'message':"You have been added to a new project by %s %s"%(request.user.first_name,request.user.last_name),
                'project':serializer.data.get("id")}
                notification=FCMSerializer(data=notification_data)
                notification.is_valid(raise_exception=True)
                notification.save()
                data_object= {
                        "title": "New Project Added",
                        "message": "You have been added to a new project by %s %s"%(request.user.first_name,request.user.last_name),
                        "notification_type":"project_assigned_client",
                        "project_id":serializer.data.get("id"),
                        "receiver_id":client.id,
                        "sender_id":request.user.id,
                        "fromNotification":True
                }
                send_notification_thread(User.objects.get(pk=notification_data.get("receiver_id")),data_object.get("title"),data_object.get("message"),data_object,len(FcmNotifications.objects.filter(receiver_id=notification_data.get("receiver_id"),watch="false")),request)
                return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
            except Exception as e:
                print(e)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        return Response(data='project can only be created through client and builder', status=status.HTTP_400_BAD_REQUEST)            

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(
            self.get_queryset()).order_by('-created_date')
        if request.query_params.get('status'):
            project_status = request.query_params['status']
            queryset = queryset.filter(status=project_status)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(methods=['get'],detail=False,url_path='trialended',url_name='trialended')
    def trialended(self, request, *args, **kwargs):
        user=User.objects.get(id=self.request.user.id)
        if user.trial_ended==date.today() and user.is_subscription=="TRIAL":
            user.is_subscription="NO_ACTIVE_PLAN"
            user.save()
            serializer = LoginSerializer(instance=user)
            return Response(data=serializer.data,status=status.HTTP_200_OK)
        return Response('Still have time for Trial Period.', status=status.HTTP_200_OK)

    @action(methods=['GET'], detail=False, url_path='retrieve', url_name='retrieve_project')
    def retrieve_project(self, request, *args, **kwargs):
        if request.query_params.get('project_id'):
            try:
                instance = self.get_queryset().get(
                    pk=request.query_params['project_id'])
            except:
                return Response('Not found.', status=status.HTTP_404_NOT_FOUND)
        else:
            return Response('Please specify a project ID.', status=status.HTTP_404_NOT_FOUND)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
        
    @action(methods=['GET'], detail=False, url_path='projectusers', url_name='projectusers')
    def projectusers(self, request, *args, **kwargs):
        if request.query_params.get('project_id'):
            try:
                instance = self.get_queryset().get(
                    pk=request.query_params['project_id'])
            except:
                return Response('Not found.', status=status.HTTP_404_NOT_FOUND)
        else:
            return Response('Please specify a project ID.', status=status.HTTP_404_NOT_FOUND)
        serializer = self.get_serializer(instance)
        builder_temp=serializer.data.get('builder')
        client_temp=serializer.data.get('client')
        worker_temp=serializer.data.get('worker')
        worker_temp.insert(0,builder_temp)
        worker_temp.insert(0,client_temp)
        return Response(worker_temp)

    @action(detail=False, methods=['get'], url_path='addworker', url_name='add_worker')
    def add_worker(self, request, *args, **kwargs):
        q = request.query_params
        if not q.get('project_id') or not q.get('worker_id'):
            return Response(data='Invalid/Incomplete data', status=status.HTTP_400_BAD_REQUEST)
        project = Project.objects.get(pk=q.get('project_id'))
        worker = User.objects.get(pk=q.get('worker_id'))
        project.worker.add(worker)
        project.save()
        serializer = ProjectDetailsSerializer(instance=project)
        try:
            notification_data={'title':'Project Assigned',
            'sender_id':request.user.id,
            'receiver_id':User.objects.get(pk=q.get('worker_id')).id,
            "project":Project.objects.get(pk=q.get('project_id')).id,
            'notification_type':"project_assigned_worker",
            'message':"You have been assigned to new project %s by %s %s"%(Project.objects.get(pk=q.get('project_id')).name,request.user.first_name,request.user.last_name)}  
            notification=FCMSerializer(data=notification_data)
            notification.is_valid(raise_exception=True)
            notification.save()
            data_object= {
                "title": "Project Assigned",
                "message": "You have been assigned to new project %s by %s %s"%(Project.objects.get(pk=q.get('project_id')).name,request.user.first_name,request.user.last_name),
                "notification_type":"project_assigned_worker",
                "project_id":Project.objects.get(pk=q.get('project_id')).id,
                "receiver_id":User.objects.get(pk=q.get('worker_id')).id,
                "sender_id":request.user.id,
                "fromNotification":True
            }
            send_notification_thread(User.objects.get(pk=notification_data.get("receiver_id")),data_object.get("title"),data_object.get("message"),data_object,len(FcmNotifications.objects.filter(receiver_id=notification_data.get("receiver_id"),watch="false")),request)
        except Exception as e:
            print(e)
        try:
            notification_data={'title':'Worker Assigned',
            'sender_id':request.user.id,
            'receiver_id':Project.objects.get(pk=q.get('project_id')).client.id,
            'project':Project.objects.get(pk=q.get('project_id')).id,
            'notification_type':"worker_assigned_project",
            'message':"A new worker %s %s has been assigned to %s project "%(User.objects.get(pk=q.get('worker_id')).first_name,User.objects.get(pk=q.get('worker_id')).last_name,Project.objects.get(pk=q.get('project_id')).name)}  
            notification=FCMSerializer(data=notification_data)
            notification.is_valid(raise_exception=True)
            notification.save()
            data_object= {
                "title": "Worker Assigned",
                "message": "A new worker %s %s has been assigned to %s project "%(User.objects.get(pk=q.get('worker_id')).first_name,User.objects.get(pk=q.get('worker_id')).last_name,Project.objects.get(pk=q.get('project_id')).name),
                "notification_type":"worker_assigned_project",
                "project_id":Project.objects.get(pk=q.get('project_id')).id,
                "receiver_id":Project.objects.get(pk=q.get('project_id')).client.id,
                "sender_id":request.user.id,
                "fromNotification":True
            }
            send_notification_thread(User.objects.get(pk=notification_data.get("receiver_id")),data_object.get("title"),data_object.get("message"),data_object,len(FcmNotifications.objects.filter(receiver_id=notification_data.get("receiver_id"),watch="false")),request)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            print(e)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['delete'], url_path="removeworker",url_name="remove_worker")
    def remove_worker(self, request,*args, **kwargs): 
        q = request.query_params
        if not q.get('project_id') or not q.get('worker_id'):
            return Response(data='Invalid/Incomplete data', status=status.HTTP_400_BAD_REQUEST)
        obj=ProjectWorker.objects.filter(project_id=q.get('project_id'),worker_id=q.get('worker_id')).delete()
        return Response(data="Worker Removed Successfully", status=status.HTTP_200_OK) 
    
    @action(detail=True, methods=['get'])
    def get_tasks(self, request, pk=None):
        tasks = Task.objects.filter(project=pk).order_by("-id")
        serializer = TasksListSerializer(tasks, many=True)

        page = self.paginate_queryset(tasks)
        if page is not None:
            serializer = TasksListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = TasksListSerializer(tasks, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(methods=['get'], detail= False, url_path='listjob')
    def leave_project_list(self, request):  
        obj = ProjectWorker.objects.filter(worker=request.user)
        serializer = ProjectWorkerSerializer(obj, many=True)
        page = self.paginate_queryset(obj)
        if page is not None:
            serializer = ProjectWorkerSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = ProjectWorkerSerializer(obj, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(methods=['get'], detail=False, url_path='leavejob')
    def leave_job(self, request,  *args, **kwargs):
        q = request.query_params
        if not q.get('project_id') :
            return Response(data='Invalid/Incomplete data', status=status.HTTP_400_BAD_REQUEST)
        tasks=Task.objects.filter(project_id=Project.objects.get(pk=q.get('project_id')),assigned_worker=request.user)
        result=0
        for i in  range(len(tasks)):
            if tasks[i].complete_status=='verified':
                result+=1
        if result==len(tasks):
            try:
                notification_data={'title':'Worker Left Project ',
                'sender_id':request.user.id,
                'receiver_id':Project.objects.get(pk=q.get('project_id')).builder.id,
                'project':q.get('project_id'),
                'notification_type':"project_leave",
                'message':" %s %s left %s project"%(request.user.first_name,request.user.last_name,Project.objects.get(pk=q.get('project_id')).name)}  
                notification=FCMSerializer(data=notification_data)
                notification.is_valid(raise_exception=True)
                notification.save()
                data_object= {
                    "title": "Worker Left Project",
                    "message": " %s %s left %s project"%(request.user.first_name,request.user.last_name,Project.objects.get(pk=q.get('project_id')).name),
                    "notification_type":"project_leave",
                    "project_id":q.get('project_id'),
                    "receiver_id":Project.objects.get(pk=q.get('project_id')).builder.id,
                    "sender_id":request.user.id,
                    "fromNotification":True
                }
                send_notification_thread(User.objects.get(pk=notification_data.get("receiver_id")),data_object.get("title"),data_object.get("message"),data_object,len(FcmNotifications.objects.filter(receiver_id=notification_data.get("receiver_id"),watch="false")),request)
                obj = ProjectWorker.objects.get(
                    project=Project.objects.get(pk=q.get('project_id')),worker=request.user).delete()
                return Response(data='Leave JOB Successfully.', status=status.HTTP_200_OK)
            except Exception as e:
                print(e)
            obj = ProjectWorker.objects.get(
                    project=Project.objects.get(pk=q.get('project_id')),worker=request.user).delete()
            return Response(data='Leave JOB Successfully.', status=status.HTTP_200_OK)
        else:
                return Response(data='your all tasks are not verfied yet so you cannot leave Project.', status=status.HTTP_401_UNAUTHORIZED)
    
    @action(methods=['get'],detail=False,url_path='archivelist')
    def archive_list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(
            self.get_queryset()).order_by('-created_date')
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    @action(methods=['get'],detail=False,url_path='deletelist')
    def delete_list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(
            self.get_queryset()).order_by('-created_date')
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(methods=['delete'], detail=True, url_path="")
    def delete(self, request, *args, **kwargs):
        query = request.query_params
        project = Project.objects.get(pk=query.get('project_id'))
        if project.status == 'archive':
            workers=ProjectWorker.objects.filter(project_id=query.get('project_id'))
            workers=[x.worker.id for x in workers]
            client=Project.objects.get(pk=query.get('project_id')).client.id
            receivers=workers+[client]
            for i in receivers:
                try:
                    notification_data={'title':'Project Deleted',
                    'sender_id':request.user.id,
                    'receiver_id':i,
                    'notification_type':"project_deleted",
                    'message':"%s project has been deleted by %s %s"%(Project.objects.get(pk=query.get('project_id')).name,request.user.first_name,request.user.last_name)}  
                    notification=FCMSerializer(data=notification_data)
                    notification.is_valid(raise_exception=True)
                    notification.save()
                    data_object= {
                        "title": "Project Deleted",
                        "message": "%s project has been deleted by %s %s"%(Project.objects.get(pk=query.get('project_id')).name,request.user.first_name,request.user.last_name),
                        "notification_type":"project_deleted",
                        "project_id":query.get('project_id'),
                        "receiver_id":i,
                        "sender_id":request.user.id,
                        "fromNotification":True
                    }
                    send_notification_thread(User.objects.get(pk=notification_data.get("receiver_id")),data_object.get("title"),data_object.get("message"),data_object,len(FcmNotifications.objects.filter(receiver_id=notification_data.get("receiver_id"),watch="false")),request)
                except Exception as e:
                    print(e)
            if project.status == 'archive':
                worker=ProjectWorker.objects.filter(
                    project=Project.objects.get(pk=query.get('project_id'))).delete()
                document=Document.objects.filter(
                    project=Project.objects.get(pk=query.get('project_id')))
                variations=Variations.objects.filter(
                    project=Project.objects.get(pk=query.get('project_id')))
                roi=ROI.objects.filter(
                    project=Project.objects.get(pk=query.get('project_id')))
                eot=EOT.objects.filter(
                    project=Project.objects.get(pk=query.get('project_id')))
                toolbox=ToolBox.objects.filter(
                    project=Project.objects.get(pk=query.get('project_id')))
                punchlist=PunchList.objects.filter(
                    project=Project.objects.get(pk=query.get('project_id')))
                for i in document:
                    files=Files.objects.filter(document=Document.objects.get(pk=i.id)).delete()
                    instance = Document.objects.get(pk=i.id).delete()
                for i in variations:
                    receivers=VariationReceiver.objects.filter(variation=Variations.objects.get(pk=i.id)).delete()
                    instance = Variations.objects.get(pk=i.id).delete()
                for i in roi:
                    receivers=ROIReceiver.objects.filter(roi=ROI.objects.get(pk=i.id)).delete()
                    instance = ROI.objects.get(pk=i.id).delete()
                for i in eot:
                    receivers=EOTReceiver.objects.filter(eot=EOT.objects.get(pk=i.id)).delete()
                    instance = EOT.objects.get(pk=i.id).delete()
                for i in toolbox:
                    receivers=ToolBoxReceiver.objects.filter(toolbox=ToolBox.objects.get(pk=i.id)).delete()
                    instance = ToolBox.objects.get(pk=i.id).delete()
                for i in punchlist:
                    receivers=PunchListReceiver.objects.filter(punchlist=PunchList.objects.get(pk=i.id)).delete()
                    checklist=CheckListPunchList.objects.filter(punchlist=PunchList.objects.get(pk=i.id)).delete()
                    instance = PunchList.objects.get(pk=i.id).delete()
            project = Project.objects.get(pk=query.get('project_id')).delete()
            return Response(data="Project Deleted Successfully", status=status.HTTP_200_OK)
        return Response(data="Only Archived Projects can be deleted", status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['get'], detail=False, url_path='archive')
    def archive(self, request,*args, **kwargs):
        q = request.query_params
        if not q.get('project_id') :
            return Response(data='Invalid/Incomplete data', status=status.HTTP_400_BAD_REQUEST)
        obj = Project.objects.get(pk=q.get('project_id'),builder=request.user)
        obj.status = 'archive'
        obj.save()
        workers=ProjectWorker.objects.filter(project_id=q.get('project_id'))
        workers=[x.worker.id for x in workers]
        client=Project.objects.get(pk=q.get('project_id')).client.id
        receivers=workers+[client]
        for i in receivers:
            try:
                notification_data={'title':'Project Archived',
                'sender_id':request.user.id,
                'receiver_id':i,
                "project":q.get('project_id'),
                'notification_type':"project_archived",
                'message':"%s project has been archived by %s %s"%(Project.objects.get(pk=q.get('project_id')).name,request.user.first_name,request.user.last_name)}  
                notification=FCMSerializer(data=notification_data)
                notification.is_valid(raise_exception=True)
                notification.save()
                data_object= {
                    "title": "Project Archived",
                    "message": "%s project has been archived by %s %s"%(Project.objects.get(pk=q.get('project_id')).name,request.user.first_name,request.user.last_name),
                    "notification_type":"project_archived",
                    "project_id":q.get('project_id'),
                    "receiver_id":i,
                    "sender_id":request.user.id,
                    "fromNotification":True
                }
                send_notification_thread(User.objects.get(pk=notification_data.get("receiver_id")),data_object.get("title"),data_object.get("message"),data_object,len(FcmNotifications.objects.filter(receiver_id=notification_data.get("receiver_id"),watch="false")),request)
            except Exception as e:
                print(e)
        return Response(data='Project Archived Successfully.', status=status.HTTP_200_OK)

    @action(methods=['get'], detail=False, url_path='completed')
    def completed(self, request,*args, **kwargs):
        q = request.query_params
        if not q.get('project_id') :
            return Response(data='Invalid/Incomplete data', status=status.HTTP_400_BAD_REQUEST)
        obj = Project.objects.get(pk=q.get('project_id'),builder=request.user)
        obj.status = 'completed'
        obj.save()
        workers=ProjectWorker.objects.filter(project_id=q.get('project_id'))
        workers=[x.worker.id for x in workers]
        client=Project.objects.get(pk=q.get('project_id')).client.id
        receivers=workers+[client]
        for i in receivers:
            try:
                notification_data={'title':'Project Completed',
                'sender_id':request.user.id,
                'receiver_id':i,
                'project':q.get('project_id'),
                'notification_type':"project_completed",
                'message':"%s project has been completed by %s %s"%(Project.objects.get(pk=q.get('project_id')).name,request.user.first_name,request.user.last_name)}  
                notification=FCMSerializer(data=notification_data)
                notification.is_valid(raise_exception=True)
                notification.save()
                data_object= {
                    "title": "Project Completed",
                    "message": "%s project has been completed by %s %s"%(Project.objects.get(pk=q.get('project_id')).name,request.user.first_name,request.user.last_name),
                    "notification_type":"project_completed",
                    "project_id":q.get('project_id'),
                    "receiver_id":i,
                    "sender_id":request.user.id,
                    "fromNotification":True
                }
                send_notification_thread(User.objects.get(pk=notification_data.get("receiver_id")),data_object.get("title"),data_object.get("message"),data_object,len(FcmNotifications.objects.filter(receiver_id=notification_data.get("receiver_id"),watch="false")),request)
            except Exception as e:
                print(e)
        return Response(data='Project completed Successfully.', status=status.HTTP_200_OK)

    @action(methods=['get'], detail=False, url_path='paused')
    def paused(self, request,*args, **kwargs):
        q = request.query_params
        if not q.get('project_id') :
            return Response(data='Invalid/Incomplete data', status=status.HTTP_400_BAD_REQUEST)
        obj = Project.objects.get(pk=q.get('project_id'),builder=request.user)
        obj.status = 'paused'
        obj.save()
        workers=ProjectWorker.objects.filter(project_id=q.get('project_id'))
        workers=[x.worker.id for x in workers]
        client=Project.objects.get(pk=q.get('project_id')).client.id
        receivers=workers+[client]
        for i in receivers:
            try:
                notification_data={'title':'Project Paused',
                'sender_id':request.user.id,
                'receiver_id':i,
                'project':q.get('project_id'),
                'notification_type':"project_paused",
                'message':"%s project has been paused by %s %s"%(Project.objects.get(pk=q.get('project_id')).name,request.user.first_name,request.user.last_name)}  
                notification=FCMSerializer(data=notification_data)
                notification.is_valid(raise_exception=True)
                notification.save()
                data_object= {
                    "title": "Project Paused",
                    "message": "%s project has been paused by %s %s"%(Project.objects.get(pk=q.get('project_id')).name,request.user.first_name,request.user.last_name),
                    "notification_type":"project_paused",
                    "project_id":q.get('project_id'),
                    "receiver_id":i,
                    "sender_id":request.user.id,
                    "fromNotification":True
                    }
                send_notification_thread(User.objects.get(pk=notification_data.get("receiver_id")),data_object.get("title"),data_object.get("message"),data_object,len(FcmNotifications.objects.filter(receiver_id=notification_data.get("receiver_id"),watch="false")),request)
            except Exception as e:
                print(e)
        return Response(data='Project paused Successfully.', status=status.HTTP_200_OK)

    @action(methods=['get'], detail=False, url_path='resume')
    def resume(self, request,*args, **kwargs):
        q = request.query_params
        if not q.get('project_id') :
                return Response(data='Invalid/Incomplete data', status=status.HTTP_400_BAD_REQUEST)
        obj = Project.objects.get(pk=q.get('project_id'),builder=request.user)
        if obj.status == 'paused':
            obj.status = 'in_progress'
            obj.save()
            workers=ProjectWorker.objects.filter(project_id=q.get('project_id'))
            workers=[x.worker.id for x in workers]
            client=Project.objects.get(pk=q.get('project_id')).client.id
            receivers=workers+[client]
            for i in receivers:
                try:
                    notification_data={'title':'Project Resumed',
                    'sender_id':request.user.id,
                    'receiver_id':i,
                    'project':q.get('project_id'),
                    'notification_type':"project_resumed",
                    'message':"%s project has been resumed by %s %s"%(Project.objects.get(pk=q.get('project_id')).name,request.user.first_name,request.user.last_name)}  
                    notification=FCMSerializer(data=notification_data)
                    notification.is_valid(raise_exception=True)
                    notification.save()
                    data_object= {
                        "title": "Project Resumed",
                        "message": "%s project has been resumed by %s %s"%(Project.objects.get(pk=q.get('project_id')).name,request.user.first_name,request.user.last_name),
                        "notification_type":"project_resumed",
                        "project_id":q.get('project_id'),
                        "receiver_id":i,
                        "sender_id":request.user.id,
                        "fromNotification":True
                    }
                    send_notification_thread(User.objects.get(pk=notification_data.get("receiver_id")),data_object.get("title"),data_object.get("message"),data_object,len(FcmNotifications.objects.filter(receiver_id=notification_data.get("receiver_id"),watch="false")),request)
                except Exception as e:
                    print(e)
            return Response(data='Project Resumed Successfully.', status=status.HTTP_200_OK)
        return Response(data='This Project is Not Paused.', status=status.HTTP_400_BAD_REQUEST)

    
    @action(methods=['get'], detail=True, url_path="assigned_workers")
    def assigned_workers(self, request, pk, *args, **kwargs):
        self.search_fields = ['first_name', 'last_name', 'email']
        client = Project.objects.get(pk=self.kwargs['pk']).client
        client = {'id': client.id, 'first_name': client.first_name, 'last_name': client.last_name,
                  'email': client.email, 'phone': client.phone,'safety_card':client.safety_card,'trade_licence':client.trade_licence, 'profile_picture': client.profile_picture}
        workers = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(workers)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
        else:
            serializer = self.get_serializer(workers, many=True)
        res = self.get_paginated_response(serializer.data)
        res.data['results'] = {'workers': serializer.data, 'client': client}
        return res
            
    @action(methods=['get'], detail=True, url_path="unassigned_workers")
    def unassigned_workers(self, request, *args, **kwargs):
        self.search_fields = ['first_name', 'last_name', 'email']
        workers = self.filter_queryset(self.get_queryset()).order_by("-id")
        page = self.paginate_queryset(workers)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
        else:
            serializer = self.get_serializer(workers, many=True)
        return self.get_paginated_response(serializer.data)

    @action(methods=['GET'],detail=False,url_path='count',url_name='count')
    def count(self, request, *args, **kwargs):
        if request.query_params.get('project_id') and self.request.user.user_type=="builder":
            count={}
            data=builder_count(self,request,count)
            print(data)
            return Response(data=data, status=status.HTTP_200_OK)
        if request.query_params.get('project_id') and self.request.user.user_type=="worker":
            count={}
            data=worker_count(self,request,count)
            print(data)
            return Response(data=data, status=status.HTTP_200_OK)
        
        if request.query_params.get('project_id') and self.request.user.user_type=="client":
            count={}
            data=client_count(self,request,count)
            print(data)
            return Response(data=data, status=status.HTTP_200_OK)
        return Response(data='Please Specify project_id', status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['GET'],detail=False,url_path='countclear',url_name='count_clear')
    def count_clear(self, request, *args, **kwargs):
        """Builder"""
        if request.query_params.get('project_id') and self.request.user.user_type=="builder" and request.query_params.get('type'):
            if request.query_params.get('type')=="variations":
                variations_sender=Variations.objects.filter(
                        sender=self.request.user,
                        project=request.query_params['project_id'],sender_watch="false")
                for i in variations_sender:
                    i.sender_watch="true"
                    i.save()
                variations_receiver=VariationReceiver.objects.filter(
                        receiver=self.request.user,
                        variation__project=request.query_params['project_id'],receiver_watch="false")
                for i in variations_receiver:
                    i.receiver_watch="true"
                    i.save()
                count={}
                data=builder_count(self,request,count)
                return Response(data=data, status=status.HTTP_200_OK)
            if request.query_params.get('type')=="specifications_and_product_information":
                specifications_and_product_information=Document.objects.filter(
                        project__builder=self.request.user,project=request.query_params['project_id'],
                        builder_watch="false",type="specifications_and_product_information")   
                for i in specifications_and_product_information:
                    i.builder_watch="true"
                    i.save()
                count={}
                data=builder_count(self,request,count)
                return Response(data=data, status=status.HTTP_200_OK)
            if request.query_params.get('type')=="site_risk_assessment":
                site_risk_assessment=SiteRiskAssessment.objects.filter(
                        project__builder=self.request.user,project=request.query_params['project_id'],
                        builder_watch="false")   
                for i in site_risk_assessment:
                    i.builder_watch="true"
                    i.save()
                count={}
                data=builder_count(self,request,count)
                return Response(data=data, status=status.HTTP_200_OK)
            if request.query_params.get('type')=="eot":
                eot_sender=EOT.objects.filter(
                        sender=self.request.user,
                        project=request.query_params['project_id'],sender_watch="false")  
                for i in eot_sender:
                    i.sender_watch="true"
                    i.save()
                eot_receiver=EOTReceiver.objects.filter(
                        receiver=self.request.user,
                        eot__project=request.query_params['project_id'],receiver_watch="false")
                for i in eot_receiver:
                    i.receiver_watch="true"
                    i.save()
                count={}
                data=builder_count(self,request,count)
                return Response(data=data, status=status.HTTP_200_OK)
            if request.query_params.get('type')=="toolbox":
                toolbox_sender=ToolBox.objects.filter(
                        sender=self.request.user,
                        project=request.query_params['project_id'],sender_watch="false")  
                for i in toolbox_sender:
                    i.sender_watch="true"
                    i.save()
                toolbox_receiver=ToolBoxReceiver.objects.filter(
                        receiver=self.request.user,
                        toolbox__project=request.query_params['project_id'],receiver_watch="false")
                for i in toolbox_receiver:
                    i.receiver_watch="true"
                    i.save()
                count={}
                data=builder_count(self,request,count)
                return Response(data=data, status=status.HTTP_200_OK)
            if request.query_params.get('type')=="roi":
                roi_sender=ROI.objects.filter(
                        sender=self.request.user,
                        project=request.query_params['project_id'],sender_watch="false") 
                for i in roi_sender:
                    i.sender_watch="true"
                    i.save()
                roi_receiver=ROIReceiver.objects.filter(
                        receiver=self.request.user,
                        roi__project=request.query_params['project_id'],receiver_watch="false")
                for i in roi_receiver:
                    i.receiver_watch="true"
                    i.save()
                count={}
                data=builder_count(self,request,count)
                return Response(data=data, status=status.HTTP_200_OK)
            if request.query_params.get('type')=="punchlist":
                punchlist_sender=PunchList.objects.filter(
                        sender=self.request.user,
                        project=request.query_params['project_id'],sender_watch="false") 
                for i in punchlist_sender:
                    i.sender_watch="true"
                    i.save()
                punchlist_receiver=PunchListReceiver.objects.filter(
                        receiver=self.request.user,
                        punchlist__project=request.query_params['project_id'],receiver_watch="false")
                for i in punchlist_receiver:
                    i.receiver_watch="true"
                    i.save()
                count={}
                data=builder_count(self,request,count)
                return Response(data=data, status=status.HTTP_200_OK)
            if request.query_params.get('type')=="people":
                people=ProjectWorker.objects.filter(project__builder=self.request.user,
                    project=request.query_params['project_id'],builder_watch="false")
                for i in people:
                    i.builder_watch="true"
                    i.save()
                count={}
                data=builder_count(self,request,count)
                return Response(data=data, status=status.HTTP_200_OK)        
            if request.query_params.get('type')=="task":
                task=Task.objects.filter(project__builder=self.request.user,
                        project=request.query_params['project_id'],builder_watch="false")
                for i in task:
                    i.builder_watch="true"
                    i.save()
                count={}
                data=builder_count(self,request,count)
                return Response(data=data, status=status.HTTP_200_OK)  
            if request.query_params.get('type')=="schedule":
                schedule=Task.objects.filter(project__builder=self.request.user,
                        project=request.query_params['project_id'],builder_watch_schedule="false",
                        worker_action="accepted")
                for i in schedule:
                    i.builder_watch_schedule="true"
                    i.save()
                count={}
                data=builder_count(self,request,count)
                return Response(data=data, status=status.HTTP_200_OK)
            if request.query_params.get('type')=="daily_work_report":
                daily_work_report=DailyLog.objects.filter(project__builder=self.request.user,
                        project=request.query_params['project_id'],builder_watch="false")
                for i in daily_work_report:
                    i.builder_watch="true"
                    i.save()
                count={}
                data=builder_count(self,request,count)
                return Response(data=data, status=status.HTTP_200_OK)
            return Response(data='Please Specify project_id', status=status.HTTP_400_BAD_REQUEST) 

        """WORKER"""
        if request.query_params.get('project_id') and self.request.user.user_type=="worker" and request.query_params.get('type'):
            if request.query_params.get('type')=="plan":
                plan=Plan.objects.filter(project__worker=self.request.user,
                project=request.query_params['project_id'],worker_watch="false")
                for i in plan:
                    i.worker_watch="true"
                    i.save()
                count={}
                data=worker_count(self,request,count)
                return Response(data=data, status=status.HTTP_200_OK)
            if request.query_params.get('type')=="variations":
                variations_sender=Variations.objects.filter(
                        sender=self.request.user,
                        project=request.query_params['project_id'],sender_watch="false")
                for i in variations_sender:
                    i.sender_watch="true"
                    i.save()
                variations_receiver=VariationReceiver.objects.filter(
                        receiver=self.request.user,
                        variation__project=request.query_params['project_id'],receiver_watch="false")
                for i in variations_receiver:
                    i.receiver_watch="true"
                    i.save()
                count={}
                data=worker_count(self,request,count)
                return Response(data=data, status=status.HTTP_200_OK)
            if request.query_params.get('type')=="specifications_and_product_information":
                specifications_and_product_information=Document.objects.filter(
                        project__worker=self.request.user,project=request.query_params['project_id'],
                        worker_watch="false",type="specifications_and_product_information")   
                for i in specifications_and_product_information:
                    i.worker_watch="true"
                    i.save()
                count={}
                data=worker_count(self,request,count)
                return Response(data=data, status=status.HTTP_200_OK)           
            if request.query_params.get('type')=="safe_work_method_statement":
                safe_work_method_statement=Safety.objects.filter(
                        project__worker=self.request.user,project=request.query_params['project_id'],
                        worker_watch="false",type="safe_work_method_statement")   
                for i in safe_work_method_statement:
                    i.worker_watch="true"
                    i.save()
                count={}
                data=worker_count(self,request,count)
                return Response(data=data, status=status.HTTP_200_OK)
            if request.query_params.get('type')=="material_safety_data_sheets":
                material_safety_data_sheets=Safety.objects.filter(
                        project__worker=self.request.user,project=request.query_params['project_id'],
                        worker_watch="false",type="material_safety_data_sheets")   
                for i in material_safety_data_sheets:
                    i.worker_watch="true"
                    i.save()
                count={}
                data=worker_count(self,request,count)
                return Response(data=data, status=status.HTTP_200_OK)
            if request.query_params.get('type')=="work_health_and_safety_plan":
                work_health_and_safety_plan=Safety.objects.filter(
                        project__worker=self.request.user,project=request.query_params['project_id'],
                        worker_watch="false",type="work_health_and_safety_plan")   
                for i in work_health_and_safety_plan:
                    i.worker_watch="true"
                    i.save()
                count={}
                data=worker_count(self,request,count)
                return Response(data=data, status=status.HTTP_200_OK)    
            if request.query_params.get('type')=="site_risk_assessment":
                site_risk_assessment=SiteRiskAssessment.objects.filter(
                        assigned_to=self.request.user,project=request.query_params['project_id'],
                        assigned_to_watch="false")   
                for i in site_risk_assessment:
                    i.assigned_to_watch="true"
                    i.save()
                count={}
                data=worker_count(self,request,count)
                return Response(data=data, status=status.HTTP_200_OK)
            if request.query_params.get('type')=="incident_report":
                person_completing_form=IncidentReport.objects.filter(
                        person_completing_form=self.request.user,project=request.query_params['project_id'],
                        person_completing_form_watch="false")   
                for i in person_completing_form:
                    i.person_completing_form_watch="true"
                    i.save()
                witness_of_incident=IncidentReport.objects.filter(
                        witness_of_incident=self.request.user,project=request.query_params['project_id'],
                        witness_of_incident_watch="false")   
                for i in person_completing_form:
                    i.witness_of_incident_watch="true"
                    i.save()
                count={}
                data=worker_count(self,request,count)
                return Response(data=data, status=status.HTTP_200_OK)
            if request.query_params.get('type')=="eot":
                eot_sender=EOT.objects.filter(
                        sender=self.request.user,
                        project=request.query_params['project_id'],sender_watch="false")  
                for i in eot_sender:
                    i.sender_watch="true"
                    i.save()
                eot_receiver=EOTReceiver.objects.filter(
                        receiver=self.request.user,
                        eot__project=request.query_params['project_id'],receiver_watch="false")
                for i in eot_receiver:
                    i.receiver_watch="true"
                    i.save()
                count={}
                data=worker_count(self,request,count)
                return Response(data=data, status=status.HTTP_200_OK)
            if request.query_params.get('type')=="toolbox":
                toolbox_sender=ToolBox.objects.filter(
                        sender=self.request.user,
                        project=request.query_params['project_id'],sender_watch="false")  
                for i in toolbox_sender:
                    i.sender_watch="true"
                    i.save()
                toolbox_receiver=ToolBoxReceiver.objects.filter(
                        receiver=self.request.user,
                        toolbox__project=request.query_params['project_id'],receiver_watch="false")
                for i in toolbox_receiver:
                    i.receiver_watch="true"
                    i.save()
                count={}
                data=worker_count(self,request,count)
                return Response(data=data, status=status.HTTP_200_OK)
            if request.query_params.get('type')=="roi":
                roi_sender=ROI.objects.filter(
                        sender=self.request.user,
                        project=request.query_params['project_id'],sender_watch="false") 
                for i in roi_sender:
                    i.sender_watch="true"
                    i.save()
                roi_receiver=ROIReceiver.objects.filter(
                        receiver=self.request.user,
                        roi__project=request.query_params['project_id'],receiver_watch="false")
                for i in roi_receiver:
                    i.receiver_watch="true"
                    i.save()
                count={}
                data=worker_count(self,request,count)
                return Response(data=data, status=status.HTTP_200_OK)
            if request.query_params.get('type')=="punchlist":
                punchlist_sender=PunchList.objects.filter(
                        sender=self.request.user,
                        project=request.query_params['project_id'],sender_watch="false") 
                for i in punchlist_sender:
                    i.sender_watch="true"
                    i.save()
                punchlist_receiver=PunchListReceiver.objects.filter(
                        receiver=self.request.user,
                        punchlist__project=request.query_params['project_id'],receiver_watch="false")
                for i in punchlist_receiver:
                    i.receiver_watch="true"
                    i.save()
                count={}
                data=worker_count(self,request,count)
                return Response(data=data, status=status.HTTP_200_OK)
            if request.query_params.get('type')=="people":
                people=ProjectWorker.objects.filter(project__worker=self.request.user,
                    project=request.query_params['project_id'],worker_watch="false")
                for i in people:
                    i.worker_watch="true"
                    i.save()
                count={}
                data=worker_count(self,request,count)
                return Response(data=data, status=status.HTTP_200_OK)         
            if request.query_params.get('type')=="task":
                task=Task.objects.filter(project__worker=self.request.user,
                        project=request.query_params['project_id'],worker_watch="false")
                for i in task:
                    i.worker_watch="true"
                    i.save()
                count={}
                data=worker_count(self,request,count)
                return Response(data=data, status=status.HTTP_200_OK)
            if request.query_params.get('type')=="schedule":
                schedule=Task.objects.filter(project__worker=self.request.user,
                        project=request.query_params['project_id'],worker_watch_schedule="false",
                        worker_action="accepted")
                for i in schedule:
                    i.worker_watch_schedule="true"
                    i.save()
                count={}
                data=worker_count(self,request,count)
                return Response(data=data, status=status.HTTP_200_OK)
            if request.query_params.get('type')=="daily_work_report":
                daily_work_report=DailyLog.objects.filter(project__worker=self.request.user,
                        project=request.query_params['project_id'],worker_watch="false")
                for i in daily_work_report:
                    i.worker_watch="true"
                    i.save()
                count={}
                data=worker_count(self,request,count)
                return Response(data=data, status=status.HTTP_200_OK)
            return Response(data='Please Specify project_id', status=status.HTTP_400_BAD_REQUEST) 
              
        """CLIENT"""
        if request.query_params.get('project_id') and self.request.user.user_type=="client" and request.query_params.get('type'):
            if request.query_params.get('type')=="plan":
                plan=Plan.objects.filter(project__client=self.request.user,
                project=request.query_params['project_id'],client_watch="false")
                for i in plan:
                    i.client_watch="true"
                    i.save()
                count={}
                data=client_count(self,request,count)
                return Response(data=data, status=status.HTTP_200_OK)               
            if request.query_params.get('type')=="variations":
                variations_sender=Variations.objects.filter(
                        sender=self.request.user,
                        project=request.query_params['project_id'],sender_watch="false")
                for i in variations_sender:
                    i.sender_watch="true"
                    i.save()
                variations_receiver=VariationReceiver.objects.filter(
                        receiver=self.request.user,
                        variation__project=request.query_params['project_id'],receiver_watch="false")
                for i in variations_receiver:
                    i.receiver_watch="true"
                    i.save()
                count={}
                data=client_count(self,request,count)
                return Response(data=data, status=status.HTTP_200_OK)   
            if request.query_params.get('type')=="specifications_and_product_information":
                specifications_and_product_information=Document.objects.filter(
                        project__client=self.request.user,project=request.query_params['project_id'],
                        client_watch="false",type="specifications_and_product_information")   
                for i in specifications_and_product_information:
                    i.client_watch="true"
                    i.save()
                count={}
                data=client_count(self,request,count)
                return Response(data=data, status=status.HTTP_200_OK)   
            if request.query_params.get('type')=="safe_work_method_statement":
                safe_work_method_statement=Safety.objects.filter(
                        project__client=self.request.user,project=request.query_params['project_id'],
                        client_watch="false",type="safe_work_method_statement")   
                for i in safe_work_method_statement:
                    i.client_watch="true"
                    i.save()
                count={}
                data=client_count(self,request,count)
                return Response(data=data, status=status.HTTP_200_OK)
            if request.query_params.get('type')=="material_safety_data_sheets":
                material_safety_data_sheets=Safety.objects.filter(
                        project__client=self.request.user,project=request.query_params['project_id'],
                        client_watch="false",type="material_safety_data_sheets")   
                for i in material_safety_data_sheets:
                    i.client_watch="true"
                    i.save()
                count={}
                data=client_count(self,request,count)
                return Response(data=data, status=status.HTTP_200_OK)
            if request.query_params.get('type')=="work_health_and_safety_plan":
                work_health_and_safety_plan=Safety.objects.filter(
                        project__client=self.request.user,project=request.query_params['project_id'],
                        client_watch="false",type="work_health_and_safety_plan")   
                for i in work_health_and_safety_plan:
                    i.client_watch="true"
                    i.save()
                count={}
                data=client_count(self,request,count)
                return Response(data=data, status=status.HTTP_200_OK)
            if request.query_params.get('type')=="site_risk_assessment":
                site_risk_assessment=SiteRiskAssessment.objects.filter(
                        assigned_to=self.request.user,project=request.query_params['project_id'],
                        assigned_to_watch="false")   
                for i in site_risk_assessment:
                    i.assigned_to_watch="true"
                    i.save()
                count={}
                data=client_count(self,request,count)
                return Response(data=data, status=status.HTTP_200_OK)
            if request.query_params.get('type')=="incident_report":
                person_completing_form=IncidentReport.objects.filter(
                        person_completing_form=self.request.user,project=request.query_params['project_id'],
                        person_completing_form_watch="false")   
                for i in person_completing_form:
                    i.person_completing_form_watch="true"
                    i.save()
                witness_of_incident=IncidentReport.objects.filter(
                        witness_of_incident=self.request.user,project=request.query_params['project_id'],
                        witness_of_incident_watch="false")   
                for i in person_completing_form:
                    i.witness_of_incident_watch="true"
                    i.save()
                count={}
                data=client_count(self,request,count)
                return Response(data=data, status=status.HTTP_200_OK)  
            if request.query_params.get('type')=="eot":
                eot_sender=EOT.objects.filter(
                        sender=self.request.user,
                        project=request.query_params['project_id'],sender_watch="false")  
                for i in eot_sender:
                    i.sender_watch="true"
                    i.save()
                eot_receiver=EOTReceiver.objects.filter(
                        receiver=self.request.user,
                        eot__project=request.query_params['project_id'],receiver_watch="false")
                for i in eot_receiver:
                    i.receiver_watch="true"
                    i.save()
                count={}
                data=client_count(self,request,count)
                return Response(data=data, status=status.HTTP_200_OK)
            if request.query_params.get('type')=="toolbox":
                toolbox_sender=ToolBox.objects.filter(
                        sender=self.request.user,
                        project=request.query_params['project_id'],sender_watch="false")  
                for i in toolbox_sender:
                    i.sender_watch="true"
                    i.save()
                toolbox_receiver=ToolBoxReceiver.objects.filter(
                        receiver=self.request.user,
                        toolbox__project=request.query_params['project_id'],receiver_watch="false")
                for i in toolbox_receiver:
                    i.receiver_watch="true"
                    i.save()
                count={}
                data=client_count(self,request,count)
                return Response(data=data, status=status.HTTP_200_OK)
            if request.query_params.get('type')=="roi":
                roi_sender=ROI.objects.filter(
                        sender=self.request.user,
                        project=request.query_params['project_id'],sender_watch="false") 
                for i in roi_sender:
                    i.sender_watch="true"
                    i.save()
                roi_receiver=ROIReceiver.objects.filter(
                        receiver=self.request.user,
                        roi__project=request.query_params['project_id'],receiver_watch="false")
                for i in roi_receiver:
                    i.receiver_watch="true"
                    i.save()
                count={}
                data=client_count(self,request,count)
                return Response(data=data, status=status.HTTP_200_OK)
            if request.query_params.get('type')=="punchlist":
                punchlist_sender=PunchList.objects.filter(
                        sender=self.request.user,
                        project=request.query_params['project_id'],sender_watch="false") 
                for i in punchlist_sender:
                    i.sender_watch="true"
                    i.save()
                punchlist_receiver=PunchListReceiver.objects.filter(
                        receiver=self.request.user,
                        punchlist__project=request.query_params['project_id'],receiver_watch="false")
                for i in punchlist_receiver:
                    i.receiver_watch="true"
                    i.save()
                count={}
                data=client_count(self,request,count)
                return Response(data=data, status=status.HTTP_200_OK) 
            if request.query_params.get('type')=="people":
                people=ProjectWorker.objects.filter(project__client=self.request.user,
                    project=request.query_params['project_id'],client_watch="false")
                for i in people:
                    i.client_watch="true"
                    i.save()
                count={}
                data=client_count(self,request,count)
                return Response(data=data, status=status.HTTP_200_OK)           
            if request.query_params.get('type')=="task":
                task=Task.objects.filter(project__client=self.request.user,
                        project=request.query_params['project_id'],client_watch="false")
                for i in task:
                    i.client_watch="true"
                    i.save()
                count={}
                data=client_count(self,request,count)
                return Response(data=data, status=status.HTTP_200_OK)   
            if request.query_params.get('type')=="schedule":
                schedule=Task.objects.filter(project__client=self.request.user,
                        project=request.query_params['project_id'],client_watch_schedule="false",
                        worker_action="accepted")
                for i in schedule:
                    i.client_watch_schedule="true"
                    i.save()
                count={}
                data=client_count(self,request,count)
                return Response(data=data, status=status.HTTP_200_OK)   
            if request.query_params.get('type')=="daily_work_report":
                daily_work_report=DailyLog.objects.filter(project__client=self.request.user,
                        project=request.query_params['project_id'],client_watch="false")
                for i in daily_work_report:
                    i.client_watch="true"
                    i.save()
                count={}
                data=client_count(self,request,count)
                return Response(data=data, status=status.HTTP_200_OK)   
        return Response(data='Please Specify project_id', status=status.HTTP_400_BAD_REQUEST)    
       
class ClientViewSet(viewsets.GenericViewSet, mixins.ListModelMixin):
    permission_classes = [IsBuilder]
    serializer_class = ClientListSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['first_name', 'last_name', 'email']

    def get_queryset(self):
        return User.objects.filter(user_type='client',invite_id__invited_by=self.request.user.id)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset()).order_by('-id')

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
