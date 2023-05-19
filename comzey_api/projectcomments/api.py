from django.shortcuts import render
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from accounts.models import User
from rest_framework import mixins, viewsets
from projectcomments.models import Comment
from projectcomments.serializers import CommentAddSerializer, CommentListSerializer

# includes ---------------->>>>>>>>>>>>>CommentViewSet
class CommentViewSet(viewsets.GenericViewSet, mixins.ListModelMixin,mixins.CreateModelMixin):
    def get_permissions(self):
        if self.action == "create" or self.action=='list':
            return [IsAuthenticated()]
    def get_serializer_class(self):
        if self.action == 'create':
            return CommentAddSerializer
        if self.action=='list':
            return CommentListSerializer
    def get_queryset(self):
        if self.action == "list":
            if self.request.query_params.get('dailylog_id'):
                return Comment.objects.filter(dailylog=self.request.query_params['dailylog_id'])

            elif self.request.query_params.get('variation_id'):
               return Comment.objects.filter(variation=self.request.query_params['variation_id'])

            elif self.request.query_params.get('roi_id'):
                    return Comment.objects.filter(roi=self.request.query_params['roi_id'])
            
            elif self.request.query_params.get('eot_id'):
                    return Comment.objects.filter(eot=self.request.query_params['eot_id'])
            
            elif self.request.query_params.get('toolbox_id'):
                    return Comment.objects.filter(toolbox=self.request.query_params['toolbox_id'])
  
            elif self.request.query_params.get('punchlist_id'):
                    return Comment.objects.filter(punchlist=self.request.query_params['punchlist_id'])

            elif self.request.query_params.get('incident_report'):
                    return Comment.objects.filter(incident_report=self.request.query_params['incident_report'])

            elif self.request.query_params.get('site_risk_assessment'):
                    return Comment.objects.filter(site_risk_assessment=self.request.query_params['site_risk_assessment'])

    def create(self, request, *args, **kwargs):       
        data=request.data.copy()
        data['user']=request.user.id
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


    def list(self, request, *args, **kwargs):

        queryset = self.filter_queryset(
            self.get_queryset())
        if request.query_params.get('dailylog_id'):
            dailylog_id = request.query_params['dailylog_id']
            queryset = queryset.filter(dailylog_id=dailylog_id) 

        elif request.query_params.get('variation_id'):
            variation_id = request.query_params['variation_id']
            queryset = queryset.filter(variation_id=variation_id)
        
        elif request.query_params.get('roi_id'):
            roi_id = request.query_params['roi_id']
            queryset = queryset.filter(roi_id=roi_id)

        elif request.query_params.get('eot_id'):
            eot_id = request.query_params['eot_id']
            queryset = queryset.filter(eot_id=eot_id)

        elif request.query_params.get('toolbox_id'):
            toolbox_id = request.query_params['toolbox_id']
            queryset = queryset.filter(toolbox_id=toolbox_id)

        elif request.query_params.get('punchlist_id'):
            punchlist_id = request.query_params['punchlist_id']
            queryset = queryset.filter(punchlist_id=punchlist_id)
        
        elif request.query_params.get('incident_report'):
            incident_report = request.query_params['incident_report']
            queryset = queryset.filter(incident_report=incident_report)
        
        elif request.query_params.get('site_risk_assessment'):
            site_risk_assessment = request.query_params['site_risk_assessment']
            queryset = queryset.filter(site_risk_assessment=site_risk_assessment)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
