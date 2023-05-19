from django.shortcuts import render
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from datetime import datetime, timedelta, date
from dateutil import tz
import datetime
from rest_framework import mixins, viewsets
from accounts.models import User
from comzey_api.count import client_count, builder_count, worker_count
from comzey_api.custom_permissions import IsClient, IsBuilder, IsWorker
from projecttimesheets.models import Timesheet
from api.models import ProjectWorker
from projecttimesheets.serializers import TimesheetCreateSerializer,TimesheetListSerializer, TimesheetStatusSerializer, TimesheetUpdateSerializer
# includes ---------------->>>>>>>>>>>>>TimesheetViewSet
class TimesheetViewset(viewsets.GenericViewSet, mixins.ListModelMixin):
    def get_permissions(self):
        if self.action == "timesheet_status":
            return [IsWorker()]
        if self.action == "start" or self.action=="end":
            return [IsWorker()]
        if self.action == "list" :
            return [IsAuthenticated()]
        if self.action == "edit_timesheet" :
            return [IsBuilder()]
  
    def get_serializer_class(self):
        if self.action == 'list':
            return TimesheetListSerializer
        if self.action=='timesheet_status':
            return TimesheetStatusSerializer
        if self.action=='start' or self.action=='end':
            return TimesheetCreateSerializer
        if self.action=='edit_timesheet':
            return TimesheetUpdateSerializer
       
    def get_queryset(self):
        if self.action=='list':
            if self.request.user.user_type=='worker':
                return Timesheet.objects.filter(worker_id=self.request.user.id) 
            if self.request.user.user_type=='client':
                return Timesheet.objects.filter(project__client=self.request.user)
            if self.request.user.user_type=='builder':
                return Timesheet.objects.filter(project__builder=self.request.user)
        if self.request.user.user_type=='client':
            return Timesheet.objects.filter(project__client=self.request.user)   
        if self.request.user.user_type=='builder':
            return Timesheet.objects.filter(project__builder=self.request.user) 
        if self.request.user.user_type=='worker':
            return ProjectWorker.objects.filter(worker_id=self.request.user)

    @action(methods=['GET'], detail=False, url_path='status', url_name='timesheet_status')
    def timesheet_status(self, request, *args, **kwargs):
        if request.query_params.get('project_id'):
            try:
                instance = self.get_queryset().get(
                    project=self.request.query_params.get('project_id'))
            except:
                return Response('Project not found.', status=status.HTTP_404_NOT_FOUND)
        else:
            return Response('Please specify a Project ID.', status=status.HTTP_404_NOT_FOUND)
        return Response({'timesheet_status':instance.timesheet_status},status=status.HTTP_200_OK)
    
    @action(methods=['GET'], detail=False, url_path='start', url_name='start_timesheet')
    def start(self, request, *args, **kwargs):
        if request.query_params.get('project_id'):
            if request.user.user_type=='worker':
                try:
                    projectworker = self.get_queryset().get(
                        project=self.request.query_params.get('project_id'))
                    project=projectworker.id
                except:
                    return Response('project not found.', status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response('Only worker can start its timesheet.', status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response('Please specify a project ID.', status=status.HTTP_400_BAD_REQUEST)
        if  projectworker.timesheet_status=="false":
            projectworker.timesheet_status="true"
            projectworker.save()
            data = {'project':self.request.query_params.get('project_id'),'worker':self.request.user.id}
            serializer = TimesheetCreateSerializer(data=data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(data='Timesheet already started',status=status.HTTP_200_OK)
    
    @action(methods=['GET'], detail=False, url_path='end', url_name='end_timesheet')
    def end(self, request, *args, **kwargs):
        if request.query_params.get('project_id'):
            try:
                projectworker = self.get_queryset().get(
                    project=self.request.query_params.get('project_id'))
                project=projectworker.id    
            except:
                return Response('Task not found.', status=status.HTTP_404_NOT_FOUND)
        else:
            return Response('Please specify a task ID.', status=status.HTTP_404_NOT_FOUND)
        if  projectworker.timesheet_status=="true":
            projectworker.timesheet_status="false"
            projectworker.save()
            # timesheet=Timesheet.objects.filter(project_id=self.request.query_params.get('project_id'),worker_id=self.request.user.id).last()
            # timesheet.end_time=datetime.datetime.now(datetime.timezone.utc)
            # timesheet.save()
            instance=Timesheet.objects.filter(project_id=self.request.query_params.get('project_id'),worker_id=self.request.user.id).last()
            end_time=datetime.datetime.now(datetime.timezone.utc)
            serializer=self.get_serializer(instance,data={'end_time':end_time},partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.update(instance=instance,validated_data={'end_time':end_time})
            timesheet=Timesheet.objects.filter(project_id=self.request.query_params.get('project_id'),worker_id=self.request.user.id).last()
            hours=str(datetime.datetime.now(datetime.timezone.utc)-timesheet.start_time)
            end_time=datetime.datetime.now(datetime.timezone.utc)
            timesheet.worked_hours=hours
            timesheet.save()
            serializer = TimesheetCreateSerializer(instance=timesheet)              
            return Response(serializer.data)
        else:
            return Response(data='Timesheet already ended',status=status.HTTP_200_OK)

    @action(methods=['PUT'], detail=False, url_path='edit', url_name='edit_timesheet')
    def edit_timesheet(self, request, *args, **kwargs):
        queryset = self.filter_queryset(
            self.get_queryset())
        if request.query_params.get('id'):
            # request.data._mutable=True
            if request.data:
                request.data._mutable=True
                start_time= datetime.datetime.strptime(request.data['start_time'],"%Y-%m-%d %H:%M:%S")
                l=list(request.query_params.get('timezone'))
                if '-' in l:
                    index=l.index('-')
                else:
                    index=l.index(' ')
                sign=l[index]
                hours=l[index+1:index+3]
                if hours[0]=='0':
                    hours=int(hours[1])
                else:
                    hours=int("".join(hours))
                minutes=l[index+4:index+6]
                minutes=int("".join(minutes))
                if sign=='-':
                    start_time=start_time+timedelta(hours=hours,minutes=minutes)

                else :
                    start_time=start_time-timedelta(hours=hours,minutes=minutes)
                to_zone = tz.gettz('UTC')
                start_time=start_time.astimezone(to_zone)
                request.data['start_time']=start_time
                end_time= datetime.datetime.strptime(request.data['end_time'],"%Y-%m-%d %H:%M:%S")
                l=list(request.query_params.get('timezone'))
                if '-' in l:
                    index=l.index('-')
                else:
                    index=l.index(' ')
                sign=l[index]
                hours=l[index+1:index+3]
                if hours[0]=='0':
                    hours=int(hours[1])
                else:
                    hours=int("".join(hours))
                minutes=l[index+4:index+6]
                minutes=int("".join(minutes))
                if sign=='-':
                    end_time=end_time+timedelta(hours=hours,minutes=minutes)

                else :
                    end_time=end_time-timedelta(hours=hours,minutes=minutes)
                to_zone = tz.gettz('UTC')
                end_time=end_time.astimezone(to_zone)
                request.data['end_time']=end_time
                instance=queryset.get(id=request.query_params['id'])
                serializer=self.get_serializer(data=request.data)
                serializer=self.get_serializer(instance,data=request.data,partial=True)
                serializer.is_valid(raise_exception=True)
                serializer.update(instance=instance,validated_data=(request.data))
                timesheet=queryset.get(id=request.query_params['id'])
                hours=str(timesheet.end_time-timesheet.start_time)
                end_time=datetime.datetime.now(datetime.timezone.utc)
                timesheet.worked_hours=hours
                timesheet.save()
                return Response(serializer.data,status=status.HTTP_200_OK)
            else:
                return Response(data='No changes',status=status.HTTP_400_BAD_REQUEST)
  
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(
            self.get_queryset()).order_by('-id')
        data=[]
        result=[]
        if request.query_params.get('timezone'):
            if request.query_params.get('date_added') and request.query_params.get('project_id'):
                queryset= queryset.filter(project_id=request.query_params['project_id'])
                l=list(request.query_params.get('timezone'))
                if '-' in l:
                    index=l.index('-')
                else:
                    index=l.index(' ')
                sign=l[index]
                hours=l[index+1:index+3]
                if hours[0]=='0':
                    hours=int(hours[1])
                else:
                    hours=int("".join(hours))
                minutes=l[index+4:index+6]
                minutes=int("".join(minutes))
                if sign=='-':
                    for i in queryset:
                        dt=i.date_added-timedelta(hours=hours, minutes=minutes)
                        if dt.strftime("%Y-%m-%d")==request.query_params.get('date_added'):
                            data.append(i)
                else:
                    for i in queryset:
                        dt=i.date_added+timedelta(hours=hours, minutes=minutes)

                        if dt.strftime("%Y-%m-%d")==request.query_params.get('date_added'):
                            data.append(i)
                for i in data:
                    if i.worked_hours=="":
                        continue
                    else:
                        result.append(i)
                queryset=result
                # queryset = queryset.filter(project__id=request.query_params['project_id'])
                # queryset = queryset.filter(date_added__date=self.request.query_params.get('date_added'),)
                page = self.paginate_queryset(queryset)
                if page is not None:
                    serializer = self.get_serializer(page, many=True)
                    return self.get_paginated_response(serializer.data)
            else:
                if request.query_params.get('project_id'):
                    queryset = queryset.filter(project__id=request.query_params['project_id'])
                    for i in queryset:
                        if i.worked_hours=="":
                            continue
                        else:
                            result.append(i)
                    queryset=result
                    page = self.paginate_queryset(queryset)
                    if page is not None:
                        serializer = self.get_serializer(page, many=True)
                        return self.get_paginated_response(serializer.data)
                else:
                    return Response(data='Please Specify project_id', status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(data='Please Specify timezone', status=status.HTTP_400_BAD_REQUEST)
