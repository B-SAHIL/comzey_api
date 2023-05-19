from django.shortcuts import render
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from accounts.models import User
from rest_framework import mixins, viewsets
from projectnotifications.models import FcmNotifications
from projectnotifications.serializers import FCMListSerializer

# includes FCM and Content Viewsets
class FCMViewset(viewsets.GenericViewSet, mixins.ListModelMixin):
    def get_permissions(self):
        if self.action == "list" or self.action=="count" or self.action=="count_clear":
            return [IsAuthenticated()]
    def get_serializer_class(self):
        if self.action == 'list':
            return FCMListSerializer
    def get_queryset(self):
        if self.action=='list':
                return FcmNotifications.objects.filter(receiver_id=self.request.user.id) 
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(
            self.get_queryset()).order_by('-date')
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)

        return Response(serializer.data)  

    @action(methods=['GET'],detail=False,url_path='count',url_name='count')
    def count(self, request, *args, **kwargs):
       count=len(FcmNotifications.objects.filter(receiver_id=self.request.user.id,watch="false"))
       count={"notification_count":count}
       return Response(data=count, status=status.HTTP_200_OK) 
    @action(methods=['GET'],detail=False,url_path='countclear',url_name='count_clear')
    def count_clear(self, request, *args, **kwargs):
        count=FcmNotifications.objects.filter(receiver_id=self.request.user.id,watch="false")
        for i in count:
           i.watch="true"
           i.save()
        count=FcmNotifications.objects.filter(receiver_id=self.request.user.id,watch="false")
        count={"notification_count":len(count)}
        return Response(data=count, status=status.HTTP_200_OK) 

class ContentViewset(viewsets.GenericViewSet, mixins.RetrieveModelMixin):
    permission_classes=[AllowAny]
    queryset = User.objects.none()
    @action(methods=['GET'],detail=False,url_path='privacyPolicy',url_name='privacy_policy')
    def privacy_policy(self, request, *args, **kwargs):
        return render(request,'privacy_policy.html')

    @action(methods=['GET'],detail=False,url_path='userAgreement',url_name='user_agreement')
    def user_agreement(self, request, *args, **kwargs):
        return render(request,'user_agreement.html')

    @action(methods=['GET'],detail=False,url_path='termAndConditions',url_name='terms_and_conditions')
    def terms_and_conditions(self, request, *args, **kwargs):
        return render(request,'terms_and_conditions.html')
