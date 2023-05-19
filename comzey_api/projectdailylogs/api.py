from django.shortcuts import render
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from rest_framework import mixins, viewsets
import requests
from comzey_api.notifications import  send_notification_thread
from accounts.models import User
from api.models import Project
from projectnotifications.serializers import FCMSerializer
from projectnotifications.models import FcmNotifications
from projectdailylogs.models import DailyLog
from projectdailylogs.serializers import DailyLogCreateSerializer,DailyLogListSerializer
# includes -------------->>>>>DailyLogViewset
class DailyLogViewset(viewsets.GenericViewSet, mixins.CreateModelMixin, mixins.ListModelMixin):
    
    def get_permissions(self):
        if self.action == "create":
            return [IsAuthenticated()]
        if self.action == 'list':
            return [IsAuthenticated()]
        if self.action == 'update_dailylog':
            return [IsAuthenticated()]
    def get_queryset(self):
        if self.action == "list" or self.action == "create" :
            if self.request.user.user_type=='worker':
                return DailyLog.objects.filter(project__worker=self.request.user)
            if self.request.user.user_type=='client':
                return DailyLog.objects.filter(project__client=self.request.user)
            if self.request.user.user_type=='builder':
                return DailyLog.objects.filter(project__builder=self.request.user)
        if self.action == 'update_dailylog':
            if self.request.user.user_type=='worker':
                return DailyLog.objects.filter(created_by=self.request.user)
            if self.request.user.user_type=='builder':
                return DailyLog.objects.filter(project__builder=self.request.user)

    def get_serializer_class(self):
        if self.action == 'create' or 'update_dailylog':
            return DailyLogCreateSerializer
        if self.action=='list':
            return DailyLogListSerializer
        
    def  create(self, request, *args, **kwargs):
        user=request.user
        if user.user_type=='worker'or user.user_type=='builder':
            data = request.data
            URL = "https://api.openweathermap.org/data/2.5/onecall"
            params = {'exclude':'minutely,hourly,alerts','lat':{data.get('location').get('latitude')},'lon':{data.get('location').get('longitude')},'units':'metric','appid':'ef8a63f8a915eb5f80fa2848ea0add46' }

            res = requests.get(url = URL, params = params)
            api_data = res.json()
            data['weather']={
                "current":int(api_data.get('current').get('temp')),
                "maximum":int(api_data.get('daily')[0].get('temp').get('max')),
                "weather_type" : api_data.get('current').get('weather')[0].get('main'),
                "icon":f"http://openweathermap.org/img/wn/{api_data.get('current').get('weather')[0].get('icon')}@2x.png"
            }
            data["created_by"]=request.user.id
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            try:
                if user.user_type=='worker':
                    notification_data={'title':'Daily Log Created',
                    'sender_id':request.user.id,
                    'receiver_id':Project.objects.get(pk=request.data['project']).builder.id,
                    'notification_type':"daily_log_created",
                    'project':Project.objects.get(pk=request.data['project']).id,
                    'dailylog':serializer.data.get('id'),
                    'message':" A daily log has been created for %s project by %s %s"%(Project.objects.get(pk=request.data['project']).name,request.user.first_name,request.user.last_name)}  
                    notification=FCMSerializer(data=notification_data)
                    notification.is_valid(raise_exception=True)
                    notification.save()
                    data_object= {

                            "title": "Daily Log Created",

                            "message": " A daily log has been created for %s project by %s %s"%(Project.objects.get(pk=request.data['project']).name,request.user.first_name,request.user.last_name),

                            "notification_type":"daily_log_created",

                            "project_id":Project.objects.get(pk=request.data['project']).id,

                            'receiver_id':Project.objects.get(pk=request.data['project']).builder.id,

                            'dailylog':serializer.data.get('id'),

                            "sender_id":request.user.id,

                            "fromNotification":True

                    

                    }
                    send_notification_thread(User.objects.get(pk=notification_data.get("receiver_id")),data_object.get("title"),data_object.get("message"),data_object,len(FcmNotifications.objects.filter(receiver_id=notification_data.get("receiver_id"),watch="false")),request)
                    return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
            except Exception as e:
                print(e)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        return Response(data='dailylogs can only be created through worker', status=status.HTTP_400_BAD_REQUEST) 


    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(
            self.get_queryset()).order_by('-created_time')
        
        if request.query_params.get('project_id'):
            project_id = request.query_params['project_id']
            queryset = queryset.filter(project_id=project_id)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)

        return Response(serializer.data)

    @action(methods=['PUT'], detail=False, url_path='update', url_name='update_dailylog')
    def update_dailylog(self, request, *args, **kwargs):
        if request.query_params.get('dailylog_id'):
            try:
                instance = self.get_queryset().get(
                    pk=request.query_params['dailylog_id'])
            except:
                return Response('Not found.', status=status.HTTP_404_NOT_FOUND)
        else:
            return Response('Please specify a dailylog_id.', status=status.HTTP_404_NOT_FOUND)
        obj_instance=DailyLog.objects.get(pk=request.query_params['dailylog_id'])
        serializer = DailyLogCreateSerializer(instance=obj_instance, data=request.data, partial=True)
        URL = "https://api.openweathermap.org/data/2.5/onecall"
        params = {'exclude':'minutely,hourly,alerts','lat':{request.data.get('location').get('latitude')},'lon':{request.data.get('location').get('longitude')},'units':'metric','appid':'ef8a63f8a915eb5f80fa2848ea0add46' }

        res = requests.get(url = URL, params = params)
        api_data = res.json()
        request.data['weather']={
            "current":int(api_data.get('current').get('temp')),
            "maximum":int(api_data.get('daily')[0].get('temp').get('max')),
            "weather_type" : api_data.get('current').get('weather')[0].get('main'),
            "icon":f"http://openweathermap.org/img/wn/{api_data.get('current').get('weather')[0].get('icon')}@2x.png"
        }
        serializer=self.get_serializer(instance,data=request.data,partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.update(instance=instance,validated_data=(request.data))
        headers = self.get_success_headers(serializer.data)
        obj_instance=DailyLog.objects.get(pk=request.query_params['dailylog_id'])
        obj_instance.client_watch="false"
        obj_instance.save()
        obj_instance=DailyLog.objects.get(pk=request.query_params['dailylog_id'])
        obj_instance.builder_watch="false"
        obj_instance.save()
        obj_instance=DailyLog.objects.get(pk=request.query_params['dailylog_id'])
        obj_instance.worker_watch="false"
        obj_instance.save()
        return Response(serializer.data,status=status.HTTP_200_OK,headers=headers)
        