from rest_framework import mixins, viewsets
from api.models import Project, ProjectWorker
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
import datetime
from accounts.models import User
import requests
from comzey_api.count import client_count, builder_count, worker_count
from comzey_api.custom_permissions import IsClient, IsBuilder, IsWorker
from comzey_api.notifications import  send_notification_thread
from dateutil import tz
from projectdocuments.models import EOT, ROI, CheckList,  Document, EOTReceiver, Files, IncidentReport, IncidentType, PunchList, PunchListReceiver, ROIReceiver, Safety, SiteRiskAssessment, SiteRiskAssessmentQuestions, ToolBox, ToolBoxReceiver, VariationReceiver, Variations,SiteRiskAssessmentRelation
from projectdocuments.serializers import CheckListSerializer, DocumentFilesSerializer, DocumentSerializer, EOTAcceptSerializer, EOTDetailsNonUserSerializer, EOTDetailsReceiverSerializer, EOTDetailsSenderSerializer, EOTListSerializer, EOTSerializer, IncidentReportListSerializer, IncidentReportSerializer, IncidentTypeSerializer, PunchlistCreateSerializer, PunchlistDetailsNonUserSerializer, PunchlistDetailsReceiverSerializer, PunchlistDetailsSenderSerializer, PunchlistListSerializer, ROIDetailsNonUserSerializer, ROIDetailsReceiverSerializer, ROIDetailsSenderSerializer, ROIListSerializer, ROISerializer, ROISubmissionSerializer, SafetySerializer, SiteRiskAssessmentListSerializer, SiteRiskAssessmentQuestionserializer, SiteRiskAssessmentSerializer, ToolBoxDetailsNonUserSerializer, ToolBoxDetailsReceiverSerializer, ToolBoxDetailsSenderSerializer, ToolBoxListSerializer, ToolBoxSerializer, VariationsDetailsNonUserSerializer, VariationsDetailsReceiverSerializer, VariationsDetailsSenderSerializer, VariationsListSerializer, VariationsSerializer , SiteRiskAssessmentRelationSerializer, SiteRiskAssessmentRelationListSerializer,SiteRiskAssessmentThroughSerializer
from projectnotifications.serializers import FCMSerializer
from projectnotifications.models import FcmNotifications

# includes -------->>>>>>
# DocumentViewset, SafetyViewset, SiteRiskAssessmentQuestionsViewset, IncidentTypeViewset,
# IncidentReportViewset, SiteRiskAssessmentViewset, VariationsViewset, EOTViewset,
# ROIViewset, ToolBoxViewset, PunchListViewset
class DocumentViewset(viewsets.GenericViewSet, mixins.CreateModelMixin,mixins.ListModelMixin,mixins.UpdateModelMixin):
    def get_permissions(self):
        if self.action == "create" or self.action == "update_document":
            return [IsAuthenticated()]
        if self.action == "list":
            return [IsAuthenticated()]
        return [AllowAny()]

    def get_queryset(self):
        if self.action == "update_document" or self.action == "delete" or self.action=="create":
            if self.request.user.user_type=="builder":
                return Document.objects.filter(project__builder=self.request.user)
            if self.request.user.user_type=="worker" :
                return Document.objects.filter(created_by=self.request.user)
            if self.request.user.user_type=="client":
                return Document.objects.filter(project__client=self.request.user)
        if self.request.user.user_type=="builder":
            return Document.objects.filter(project__builder=self.request.user)
        if self.request.user.user_type=="client":
            return Document.objects.filter(project__client=self.request.user)
        if self.request.user.user_type=="worker":
            return Document.objects.filter(project__worker=self.request.user)
        
    def get_serializer_class(self):
        if self.action == 'create' or self.action == "update_document":
            return DocumentSerializer
        if self.action == 'list':
            return DocumentSerializer

    def create(self, request, *args, **kwargs):
        user=request.user
        if user.user_type=='worker'or user.user_type=='builder' or user.user_type=='client':
            files_data=[]
            if request.data['files_list'] !=[]:
                files=request.data['files_list']
                files_data=[]
                for i in files:
                    files = DocumentFilesSerializer(data={'file_name':i.get('file_name'),'size':i.get('file_size')})
                    files.is_valid(raise_exception=False)
                    self.perform_create(files)
                    files_data.append(files.data.get('id'))
                request.data['files_list']=files_data
            # request.data._mutable=True  
            data = request.data
            data["created_by"]=request.user.id
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            for i in files_data:    
                Doc= Document.objects.get(pk=serializer.data.get('id')) 
                files = i
                Doc.files_list.add(files)
                Doc.save()
            instance = self.get_queryset().get(
                    pk=serializer.data.get('id'))
            serializer = DocumentSerializer(instance)
            headers = self.get_success_headers(serializer.data)
            workers=ProjectWorker.objects.filter(project_id=request.data['project'])
            workers=[x.worker.id for x in workers]
            if request.user.user_type=="builder":
                client=Project.objects.get(pk=request.data['project']).client.id
                receivers=workers+[client]
                for i in receivers:
                    try:
                        notification_data={'title':'New Specification & Product Information Added',
                        'sender_id':request.user.id,
                        'receiver_id':i,
                        'notification_type':"product_information_added",
                        'product_information':serializer.data.get('id'),
                        'project':request.data['project'],
                        'message':"A new Specification And Product Information has been created for %s project by %s %s"%(Project.objects.get(pk=request.data['project']).name,request.user.first_name,request.user.last_name)}  
                        notification=FCMSerializer(data=notification_data)
                        notification.is_valid(raise_exception=True)
                        notification.save()
                        data_object= {
                                "title": "New Specification & Product Information Added",
                                "message":"A new Specification And Product Information has been created for %s project by %s %s"%(Project.objects.get(pk=request.data['project']).name,request.user.first_name,request.user.last_name),
                                "notification_type":"product_information_added",
                                "project_id":request.data['project'],
                                "receiver_id":i,
                                "product_information_id":serializer.data.get('id'),
                                "sender_id":request.user.id,
                                "fromNotification":True
                        }
                        send_notification_thread(User.objects.get(pk=notification_data.get("receiver_id")),data_object.get("title"),data_object.get("message"),data_object,len(FcmNotifications.objects.filter(receiver_id=notification_data.get("receiver_id"),watch="false")),request)
                    except Exception as e:
                        print(e)
                        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
                return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
            elif request.user.user_type=="client":
                builder=Project.objects.get(pk=request.data['project']).builder.id
                receivers=workers+[builder]
                for i in receivers:
                    try:
                        notification_data={'title':'New Specification & Product Information Added',
                        'sender_id':request.user.id,
                        'receiver_id':i, 
                        'notification_type':"product_information_added",
                        'product_information':serializer.data.get('id'),
                        'project':request.data['project'],
                        'message':"A new Specification And Product Information has been created for %s project by %s %s"%(Project.objects.get(pk=request.data['project']).name,request.user.first_name,request.user.last_name)}  
                        notification=FCMSerializer(data=notification_data)
                        notification.is_valid(raise_exception=True)
                        notification.save()
                        data_object= {
                                "title": "New Specification & Product Information Added",
                                "message":"A new Specification And Product Information has been created for %s project by %s %s"%(Project.objects.get(pk=request.data['project']).name,request.user.first_name,request.user.last_name),
                                "notification_type":"product_information_added",
                                "project_id":request.data['project'],
                                "receiver_id":i,
                                "product_information_id":serializer.data.get('id'),
                                "sender_id":request.user.id,
                                "fromNotification":True
                        }
                        send_notification_thread(User.objects.get(pk=notification_data.get("receiver_id")),data_object.get("title"),data_object.get("message"),data_object,len(FcmNotifications.objects.filter(receiver_id=notification_data.get("receiver_id"),watch="false")),request)
                    except Exception as e:
                        print(e)
                        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
                return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
            else:
                client=Project.objects.get(pk=request.data['project']).client.id
                builder=Project.objects.get(pk=request.data['project']).builder.id
                workers.remove(request.user.id)
                receivers=workers+[builder]+[client]
                for i in receivers:
                    try:
                        notification_data={'title':'New Specification & Product Information Added',
                        'sender_id':request.user.id,
                        'receiver_id':i, 
                        'notification_type':"product_information_added",
                        'product_information':serializer.data.get('id'),
                        'project':request.data['project'],
                        'message':"A new Specification And Product Information has been created for %s project by %s %s"%(Project.objects.get(pk=request.data['project']).name,request.user.first_name,request.user.last_name)}  
                        notification=FCMSerializer(data=notification_data)
                        notification.is_valid(raise_exception=True)
                        notification.save()
                        data_object= {
                                "title": "New Specification & Product Information Added",
                                "message":"A new Specification And Product Information has been created for %s project by %s %s"%(Project.objects.get(pk=request.data['project']).name,request.user.first_name,request.user.last_name),
                                "notification_type":"product_information_added",
                                "project_id":request.data['project'],
                                "receiver_id":i,
                                "product_information_id":serializer.data.get('id'),
                                "sender_id":request.user.id,
                                "fromNotification":True
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
        if request.query_params.get('type'):
            queryset = queryset.filter(
                type=self.request.query_params.get('type'))
        else:
            return Response(data='Please Specify type', status=status.HTTP_400_BAD_REQUEST)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(methods=['delete'], detail=True, url_path="")
    def delete(self, request, *args, **kwargs):
        if request.query_params.get('document_id'):
            project=Document.objects.get(pk=request.query_params['document_id']).project
            if self.request.user==Document.objects.get(pk=request.query_params.get('document_id')).created_by or self.request.user==Project.objects.get(id=project.id).builder or  self.request.user==Project.objects.get(id=project.id).client:
                project=Document.objects.get(pk=request.query_params['document_id']).project.id
                workers=ProjectWorker.objects.filter(project_id=project)
                workers=[x.worker.id for x in workers]
                if request.user.user_type=="builder":
                    client=Project.objects.get(pk=project).client.id
                    receivers=workers+[client]
                    for i in receivers:
                        try:
                            notification_data={'title':'New Specification & Product Information Deleted',
                            'sender_id':request.user.id,
                            'receiver_id':i,
                            'notification_type':"product_information_deleted",
                            'project':project,
                            'message':"Product Information %s has been deleted for %s project by %s %s"%(Document.objects.get(pk=request.query_params.get('document_id')).name,Project.objects.get(pk=project).name,request.user.first_name,request.user.last_name)}  
                            notification=FCMSerializer(data=notification_data)
                            notification.is_valid(raise_exception=True)
                            notification.save()
                            data_object= {
                                    "title": "New Specification & Product Information Deleted",
                                    "message":"Product Information %s has been deleted for %s project by %s %s"%(Document.objects.get(pk=request.query_params.get('document_id')).name,Project.objects.get(pk=project).name,request.user.first_name,request.user.last_name),
                                    "notification_type":"product_information_deleted",
                                    "project_id":project,
                                    "receiver_id":i,
                                    "sender_id":request.user.id,
                                    "fromNotification":True
                            }
                            send_notification_thread(User.objects.get(pk=notification_data.get("receiver_id")),data_object.get("title"),data_object.get("message"),data_object,len(FcmNotifications.objects.filter(receiver_id=notification_data.get("receiver_id"),watch="false")),request)
                        except Exception as e:
                            print(e)
                    files=Files.objects.filter(document=Document.objects.get(pk=request.query_params.get('document_id'))).delete()
                    instance = Document.objects.get(pk=request.query_params.get('document_id')).delete()
                    return Response(data="Document  Deleted Successfully", status=status.HTTP_200_OK)
                elif request.user.user_type=="client":
                    builder=Project.objects.get(pk=project).builder.id
                    receivers=workers+[builder]
                    for i in receivers:
                        try:
                            notification_data={'title':'New Specification & Product Information Deleted',
                            'sender_id':request.user.id,
                            'receiver_id':i, 
                            'notification_type':"product_information_deleted",
                            'project':project,
                            'message':"Product Information %s has been deleted for %s project by %s %s"%(Document.objects.get(pk=request.query_params.get('document_id')).name,Project.objects.get(pk=project).name,request.user.first_name,request.user.last_name)}  
                            notification=FCMSerializer(data=notification_data)
                            notification.is_valid(raise_exception=True)
                            notification.save()
                            data_object= {
                                    "title": "New Specification & Product Information Deleted",
                                    "message":"Product Information %s has been deleted for %s project by %s %s"%(Document.objects.get(pk=request.query_params.get('document_id')).name,Project.objects.get(pk=project).name,request.user.first_name,request.user.last_name),
                                    "notification_type":"product_information_deleted",
                                    "project":project,
                                    "receiver_id":i,
                                    "sender_id":request.user.id,
                                    "fromNotification":True
                            }
                            send_notification_thread(User.objects.get(pk=notification_data.get("receiver_id")),data_object.get("title"),data_object.get("message"),data_object,len(FcmNotifications.objects.filter(receiver_id=notification_data.get("receiver_id"),watch="false")),request)
                        except Exception as e:
                            print(e)
                    files=Files.objects.filter(document=Document.objects.get(pk=request.query_params.get('document_id'))).delete()
                    instance = Document.objects.get(pk=request.query_params.get('document_id')).delete()
                    return Response(data="Document  Deleted Successfully", status=status.HTTP_200_OK)
                else:
                    client=Project.objects.get(pk=project).client.id
                    builder=Project.objects.get(pk=project).builder.id
                    workers.remove(request.user.id)
                    receivers=workers+[builder]+[client]
                    for i in receivers:
                        try:
                            notification_data={'title':'New Specification & Product Information Deleted',
                            'sender_id':request.user.id,
                            'receiver_id':i, 
                            'notification_type':"product_information_deleted",
                            'project':project,
                            'message':"Product Information %s has been deleted for %s project by %s %s"%(Document.objects.get(pk=request.query_params.get('document_id')).name,Project.objects.get(pk=project).name,request.user.first_name,request.user.last_name)}  
                            notification=FCMSerializer(data=notification_data)
                            notification.is_valid(raise_exception=True)
                            notification.save()
                            data_object= {
                                    "title": "New Specification & Product Information Deleted",
                                    "message":"Product Information %s has been deleted for %s project by %s %s"%(Document.objects.get(pk=request.query_params.get('document_id')).name,Project.objects.get(pk=project).name,request.user.first_name,request.user.last_name),
                                    "notification_type":"product_information_deleted",
                                    "project":project,
                                    "receiver_id":i,
                                    "sender_id":request.user.id,
                                    "fromNotification":True
                            }
                            send_notification_thread(User.objects.get(pk=notification_data.get("receiver_id")),data_object.get("title"),data_object.get("message"),data_object,len(FcmNotifications.objects.filter(receiver_id=notification_data.get("receiver_id"),watch="false")),request)
                        except Exception as e:
                            print(e)
                    files=Files.objects.filter(document=Document.objects.get(pk=request.query_params.get('document_id'))).delete()
                    instance = Document.objects.get(pk=request.query_params.get('document_id')).delete()
                    return Response(data="Document  Deleted Successfully", status=status.HTTP_200_OK)
            else: 
                return Response('You dont have the access to delete this Document.', status=status.HTTP_404_NOT_FOUND)
        return Response('Please specify a Document ID.', status=status.HTTP_404_NOT_FOUND)

    @action(methods=['PUT'],detail=False,url_path='update',url_name='update_document')
    def update_document(self, request,*args, **kwargs):
        if request.query_params.get('document_id'):
            try:
                instance = self.get_queryset().get(
                    pk=request.query_params['document_id'])
            except:
                return Response('Not found.', status=status.HTTP_404_NOT_FOUND)
        else:
            return Response('Please specify a document_id.', status=status.HTTP_404_NOT_FOUND)
        files_data=[]
        if request.data['files_list'] !=[]:
            files=request.data['files_list']
            files_data=[]
            for i in files:
                files = DocumentFilesSerializer(data={'file_name':i.get('file_name'),'size':i.get('file_size')})
                files.is_valid(raise_exception=False)
                self.perform_create(files)
                files_data.append(files.data.get('id'))
            request.data['files_list']=files_data
        obj_instance=Document.objects.get(pk=request.query_params['document_id'])
        serializer = DocumentSerializer(instance=obj_instance, data=request.data, partial=True)
        serializer=self.get_serializer(instance,data=request.data,partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.update(instance=instance,validated_data=(request.data))
        headers = self.get_success_headers(serializer.data)
        obj_instance=Document.objects.get(pk=request.query_params['document_id'])
        obj_instance.worker_watch="false"
        obj_instance.save()
        obj_instance=Document.objects.get(pk=request.query_params['document_id'])
        obj_instance.builder_watch="false"
        obj_instance.save()
        obj_instance=Document.objects.get(pk=request.query_params['document_id'])
        obj_instance.client_watch="false"
        obj_instance.save()
        project=Document.objects.get(pk=request.query_params['document_id']).project
        workers=ProjectWorker.objects.filter(project_id=project.id)
        workers=[x.worker.id for x in workers]
        if request.user.user_type=="builder":
            client=Project.objects.get(pk=project.id).client.id
            receivers=workers+[client]
            for i in receivers:
                try:
                    notification_data={'title':'New Specification & Product Information Updated',
                    'sender_id':request.user.id,
                    'receiver_id':i,
                    'notification_type':"product_information_updated",
                    'product_information':serializer.data.get('id'),
                    'project':project.id,
                    'message':"Product Information %s has been updated for %s project by %s %s"%(Document.objects.get(pk=request.query_params.get('document_id')).name,Project.objects.get(pk=project.id).name,request.user.first_name,request.user.last_name)}  
                    notification=FCMSerializer(data=notification_data)
                    notification.is_valid(raise_exception=True)
                    notification.save()
                    data_object= {
                            "title": "New Specification & Product Information Updated",
                            "message":"Product Information %s has been updated for %s project by %s %s"%(Document.objects.get(pk=request.query_params.get('document_id')).name,Project.objects.get(pk=project.id).name,request.user.first_name,request.user.last_name),
                            "notification_type":"product_information_updated",
                            "project_id":project.id,
                            "receiver_id":i,
                            "product_information_id":serializer.data.get('id'),
                            "sender_id":request.user.id,
                            "fromNotification":True
                    }
                    send_notification_thread(User.objects.get(pk=notification_data.get("receiver_id")),data_object.get("title"),data_object.get("message"),data_object,len(FcmNotifications.objects.filter(receiver_id=notification_data.get("receiver_id"),watch="false")),request)
                except Exception as e:
                    print(e)
                    return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        elif request.user.user_type=="client":
            builder=Project.objects.get(pk=project.id).builder.id
            receivers=workers+[builder]
            for i in receivers:
                try:
                    notification_data={'title':'New Specification & Product Information Updated',
                    'sender_id':request.user.id,
                    'receiver_id':i, 
                    'notification_type':"product_information_updated",
                    'product_information':serializer.data.get('id'),
                    'project':project.id,
                    'message':"Product Information %s has been updated for %s project by %s %s"%(Document.objects.get(pk=request.query_params.get('document_id')).name,Project.objects.get(pk=project.id).name,request.user.first_name,request.user.last_name)}  
                    notification=FCMSerializer(data=notification_data)
                    notification.is_valid(raise_exception=True)
                    notification.save()
                    data_object= {
                            "title": "New Specification & Product Information Updated",
                            "message":"Product Information %s has been updated for %s project by %s %s"%(Document.objects.get(pk=request.query_params.get('document_id')).name,Project.objects.get(pk=project.id).name,request.user.first_name,request.user.last_name),
                            "notification_type":"product_information_updated",
                            "project_id":project.id,
                            "receiver_id":i,
                            "product_information_id":serializer.data.get('id'),
                            "sender_id":request.user.id,
                            "fromNotification":True
                    }
                    send_notification_thread(User.objects.get(pk=notification_data.get("receiver_id")),data_object.get("title"),data_object.get("message"),data_object,len(FcmNotifications.objects.filter(receiver_id=notification_data.get("receiver_id"),watch="false")),request)
                except Exception as e:
                    print(e)
                    return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        else:
            client=Project.objects.get(pk=project.id).client.id
            builder=Project.objects.get(pk=project.id).builder.id
            workers.remove(request.user.id)
            receivers=workers+[builder]+[client]
            for i in receivers:
                try:
                    notification_data={'title':'New Specification & Product Information Updated',
                    'sender_id':request.user.id,
                    'receiver_id':i, 
                    'notification_type':"product_information_updated",
                    'product_information':serializer.data.get('id'),
                    'project':project.id,
                    'message':"Product Information %s has been updated for %s project by %s %s"%(Document.objects.get(pk=request.query_params.get('document_id')).name,Project.objects.get(pk=project.id).name,request.user.first_name,request.user.last_name)}  
                    notification=FCMSerializer(data=notification_data)
                    notification.is_valid(raise_exception=True)
                    notification.save()
                    data_object= {
                            "title": "New Specification & Product Information Updated",
                            "message":"Product Information %s has been updated for %s project by %s %s"%(Document.objects.get(pk=request.query_params.get('document_id')).name,Project.objects.get(pk=project.id).name,request.user.first_name,request.user.last_name),
                            "notification_type":"product_information_updated",
                            "project_id":project.id,
                            "receiver_id":i,
                            "product_information_id":serializer.data.get('id'),
                            "sender_id":request.user.id,
                            "fromNotification":True
                    }
                    send_notification_thread(User.objects.get(pk=notification_data.get("receiver_id")),data_object.get("title"),data_object.get("message"),data_object,len(FcmNotifications.objects.filter(receiver_id=notification_data.get("receiver_id"),watch="false")),request)
                except Exception as e:
                    print(e)
                    return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

class SafetyViewset(viewsets.GenericViewSet, mixins.CreateModelMixin, mixins.DestroyModelMixin,mixins.ListModelMixin,mixins.UpdateModelMixin):
    def get_permissions(self):
        if self.action == "create" or self.action == "update_safety":
            return [IsAuthenticated()]
        if self.action == "list":
            return [IsAuthenticated()]
        return [AllowAny()]

    def get_queryset(self):
        if self.action == "update_safety" or self.action == "delete" or self.action=="create":
            if self.request.user.user_type=="builder":
                return Safety.objects.filter(project__builder=self.request.user)
            if self.request.user.user_type=="worker" :
                return Safety.objects.filter(created_by=self.request.user)
            if self.request.user.user_type=="client":
                return Safety.objects.filter(project__client=self.request.user)
        if self.request.user.user_type=="builder":
            return Safety.objects.filter(project__builder=self.request.user)
        if self.request.user.user_type=="client":
            return Safety.objects.filter(project__client=self.request.user)
        if self.request.user.user_type=="worker":
            return Safety.objects.filter(project__worker=self.request.user)
        
    def get_serializer_class(self):
        if self.action == 'create' or self.action == "update_safety":
            return SafetySerializer
        if self.action == 'list':
            return SafetySerializer

    def create(self, request, *args, **kwargs):
        user=request.user
        if user.user_type=='worker'or user.user_type=='builder' or user.user_type=='client':
            # request.data._mutable=True  
            data = request.data
            data["created_by"]=request.user.id
            serializer = self.get_serializer(data=data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            instance=Safety.objects.get(pk=serializer.data.get('id'))
            dicti={
                "id": instance.id,
                "project": {'id':instance.project.id,'name':instance.project.name,'created_date':instance.project.created_date.strftime("%Y-%m-%d %H:%M:%S" ) ,'status':instance.project.status, 'description':instance.project.description},
                "created_by":{'id':instance.created_by.id,'first_name':instance.created_by.first_name,'last_name':instance.created_by.last_name,'email':instance.created_by.email, 'phone':instance.created_by.phone,'profile_picture': instance.created_by.profile_picture},
                "name":instance.name,
                "description":instance.description,
                "file":instance.file,
                "type":instance.type,
                "created_date":instance.created_date.strftime("%Y-%m-%d %H:%M:%S" ),
                "updated_date":instance.updated_date.strftime("%Y-%m-%d %H:%M:%S" )}
            project=instance.project
            workers=ProjectWorker.objects.filter(project_id=instance.project.id)
            workers=[x.worker.id for x in workers]
            client=Project.objects.get(pk=project.id).client.id
            receivers=workers+[client]
            if instance.type=='safe_work_method_statement':
                for i in receivers:
                    try:
                        notification_data={'title':'Safety Work Method Added',
                        'sender_id':request.user.id,
                        'receiver_id':i,
                        'notification_type':"new_safety_work_method_created",
                        'safety':serializer.data.get('id'),
                        'project':project.id,
                        'message':"A new Safety Work Method has been created for %s project by %s %s"%(Project.objects.get(pk=project.id).name,request.user.first_name,request.user.last_name)}  
                        notification=FCMSerializer(data=notification_data)
                        notification.is_valid(raise_exception=True)
                        notification.save()
                        data_object= {
                                "title": "Safety Work Method Added",
                                "message":"A new Safety Work Method has been created for %s project by %s %s"%(Project.objects.get(pk=project.id).name,request.user.first_name,request.user.last_name),
                                "notification_type":"new_safety_work_method_created",
                                "project_id":project.id,
                                "receiver_id":i,
                                "safety_work_method_id":serializer.data.get('id'),
                                "sender_id":request.user.id,
                                "fromNotification":True
                        }
                        send_notification_thread(User.objects.get(pk=notification_data.get("receiver_id")),data_object.get("title"),data_object.get("message"),data_object,len(FcmNotifications.objects.filter(receiver_id=notification_data.get("receiver_id"),watch="false")),request)
                    except Exception as e:
                        print(e)
                return Response(dicti, status=status.HTTP_201_CREATED, headers=headers)
                # return Response("you are sending incomplete data", status=status.HTTP_400_BAD_REQUEST)
            elif instance.type=='material_safety_data_sheets':
                for i in receivers:
                    try:
                        notification_data={'title':' Material Safety Added ',
                        'sender_id':request.user.id,
                        'receiver_id':i,
                        'notification_type':"new_material_safety_created",
                        'safety':serializer.data.get('id'),
                        'project':project.id,
                        'message':"A new material safety  has been created for %s project by %s %s"%(Project.objects.get(pk=project.id).name,request.user.first_name,request.user.last_name)}  
                        notification=FCMSerializer(data=notification_data)
                        notification.is_valid(raise_exception=True)
                        notification.save()
                        data_object= {
                                "title": " Material Safety Added ",
                                "message":"A new material safety  has been created for %s project by %s %s"%(Project.objects.get(pk=project.id).name,request.user.first_name,request.user.last_name),
                                "notification_type":"new_material_safety_created",
                                "project_id":project.id,
                                "receiver_id":i,
                                "material_safety_id":serializer.data.get('id'),
                                "sender_id":request.user.id,
                                "fromNotification":True
                        }
                        send_notification_thread(User.objects.get(pk=notification_data.get("receiver_id")),data_object.get("title"),data_object.get("message"),data_object,len(FcmNotifications.objects.filter(receiver_id=notification_data.get("receiver_id"),watch="false")),request)
                    except Exception as e:
                        print(e)
                return Response(dicti, status=status.HTTP_201_CREATED, headers=headers)
            else:
                for i in receivers:
                    try:
                        notification_data={'title':' Work Health Added ',
                        'sender_id':request.user.id,
                        'receiver_id':i,
                        'notification_type':"new_work_health_created",
                        'safety':serializer.data.get('id'),
                        'project':project.id,
                        'message':"A new work health has been created for %s project by %s %s"%(Project.objects.get(pk=project.id).name,request.user.first_name,request.user.last_name)}  
                        notification=FCMSerializer(data=notification_data)
                        notification.is_valid(raise_exception=True)
                        notification.save()
                        data_object= {
                                "title": " Work Health Added ",
                                "message":"A new work health has been created for %s project by %s %s"%(Project.objects.get(pk=project.id).name,request.user.first_name,request.user.last_name),
                                "notification_type":"new_work_health_created",
                                "project_id":project.id,
                                "receiver_id":i,
                                "work_health_id":serializer.data.get('id'),
                                "sender_id":request.user.id,
                                "fromNotification":True
                        }
                        send_notification_thread(User.objects.get(pk=notification_data.get("receiver_id")),data_object.get("title"),data_object.get("message"),data_object,len(FcmNotifications.objects.filter(receiver_id=notification_data.get("receiver_id"),watch="false")),request)
                    except Exception as e:
                        print(e)
                return Response(dicti, status=status.HTTP_201_CREATED, headers=headers)
        return Response("you are sending incomplete data", status=status.HTTP_400_BAD_REQUEST)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(
            self.get_queryset()).order_by('-created_date')
        if request.query_params.get('project_id'):
            queryset = queryset.filter(
                project=request.query_params['project_id'])
        else:
            return Response(data='Please Specify project_id', status=status.HTTP_400_BAD_REQUEST)
        if request.query_params.get('type'):
            queryset = queryset.filter(
                type=self.request.query_params.get('type'))
        else:
            return Response(data='Please Specify type', status=status.HTTP_400_BAD_REQUEST)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(methods=['delete'], detail=True, url_path="")
    def delete(self, request, *args, **kwargs):
        if request.query_params.get('safety_id'):
            project=Safety.objects.get(id=request.query_params.get('safety_id')).project
            if self.request.user==Safety.objects.get(pk=request.query_params.get('safety_id')).created_by or self.request.user==Project.objects.get(id=project.id).builder or self.request.user==Project.objects.get(id=project.id).client:
                instance=Safety.objects.get(pk=request.query_params['safety_id'])
                workers=ProjectWorker.objects.filter(project_id=instance.project.id)
                workers=[x.worker.id for x in workers]
                client=Project.objects.get(pk=project.id).client.id
                receivers=workers+[client]
                if instance.type=='safe_work_method_statement':
                    for i in receivers:
                        try:
                            notification_data={'title':'Safety Work Method Deleted',
                            'sender_id':request.user.id,
                            'receiver_id':i,
                            'notification_type':"safety_work_method_deleted",
                            'project':project.id,
                            'message':"Safety Work Method %s has been deleted for %s project by %s %s"%(instance.name,Project.objects.get(pk=project.id).name,request.user.first_name,request.user.last_name)}  
                            notification=FCMSerializer(data=notification_data)
                            notification.is_valid(raise_exception=True)
                            notification.save()
                            data_object= {
                                    "title": "Safety Work Method Deleted",
                                    "message":"Safety Work Method %s has been deleted for %s project by %s %s"%(instance.name,Project.objects.get(pk=project.id).name,request.user.first_name,request.user.last_name),
                                    "notification_type":"safety_work_method_deleted",
                                    "project_id":project.id,
                                    "receiver_id":i,
                                    "sender_id":request.user.id,
                                    "fromNotification":True
                            }
                            send_notification_thread(User.objects.get(pk=notification_data.get("receiver_id")),data_object.get("title"),data_object.get("message"),data_object,len(FcmNotifications.objects.filter(receiver_id=notification_data.get("receiver_id"),watch="false")),request)
                        except Exception as e:
                            print(e)
                    instance = Safety.objects.get(pk=request.query_params.get('safety_id')).delete()
                    return Response(data="Safety  Deleted Successfully", status=status.HTTP_200_OK)
                elif instance.type=='material_safety_data_sheets':
                    for i in receivers:
                        try:
                            notification_data={'title':' Material Safety Deleted ',
                            'sender_id':request.user.id,
                            'receiver_id':i,
                            'notification_type':"material_safety_deleted",
                            'project':project.id,
                            'message':"Material safety %s has been deleted for %s project by %s %s"%(instance.name,Project.objects.get(pk=project.id).name,request.user.first_name,request.user.last_name)}  
                            notification=FCMSerializer(data=notification_data)
                            notification.is_valid(raise_exception=True)
                            notification.save()
                            data_object= {
                                    "title": " Material Safety Deleted ",
                                    "message":"Material safety %s has been deleted for %s project by %s %s"%(instance.name,Project.objects.get(pk=project.id).name,request.user.first_name,request.user.last_name),
                                    "notification_type":"material_safety_deleted",
                                    "project_id":project.id,
                                    "receiver_id":i,
                                    "sender_id":request.user.id,
                                    "fromNotification":True
                            }
                            send_notification_thread(User.objects.get(pk=notification_data.get("receiver_id")),data_object.get("title"),data_object.get("message"),data_object,len(FcmNotifications.objects.filter(receiver_id=notification_data.get("receiver_id"),watch="false")),request)
                        except Exception as e:
                            print(e)
                    instance = Safety.objects.get(pk=request.query_params.get('safety_id')).delete()
                    return Response(data="Safety  Deleted Successfully", status=status.HTTP_200_OK)
                else:
                    for i in receivers:
                        try:
                            notification_data={'title':'  Work Health Deleted ',
                            'sender_id':request.user.id,
                            'receiver_id':i,
                            'notification_type':"work_health_deleted",
                            'project':project.id,
                            'message':"Work health %s has been deleted for %s project by %s %s"%(instance.name,Project.objects.get(pk=project.id).name,request.user.first_name,request.user.last_name)}  
                            notification=FCMSerializer(data=notification_data)
                            notification.is_valid(raise_exception=True)
                            notification.save()
                            data_object= {
                                    "title": " Work Health Deleted ",
                                    "message":"Work health %s has been deleted for %s project by %s %s"%(instance.name,Project.objects.get(pk=project.id).name,request.user.first_name,request.user.last_name),
                                    "notification_type":"work_health_deleted",
                                    "project_id":project.id,
                                    "receiver_id":i,
                                    "sender_id":request.user.id,
                                    "fromNotification":True
                            }
                            send_notification_thread(User.objects.get(pk=notification_data.get("receiver_id")),data_object.get("title"),data_object.get("message"),data_object,len(FcmNotifications.objects.filter(receiver_id=notification_data.get("receiver_id"),watch="false")),request)
                        except Exception as e:
                            print(e)
                    instance = Safety.objects.get(pk=request.query_params.get('safety_id')).delete()
                    return Response(data="Safety  Deleted Successfully", status=status.HTTP_200_OK)
            else: 
                return Response('You dont have the access to delete this Safety.', status=status.HTTP_404_NOT_FOUND)
        return Response('Please specify a Safety ID.', status=status.HTTP_404_NOT_FOUND)

    @action(methods=['PUT'],detail=False,url_path='update',url_name='update_safety')
    def update_safety(self, request,*args, **kwargs):
        if request.query_params.get('safety_id'):
            try:
                instance = self.get_queryset().get(
                    pk=request.query_params['safety_id'])
            except:
                return Response('Not found.', status=status.HTTP_404_NOT_FOUND)
        else:
            return Response('Please specify a safety_id.', status=status.HTTP_404_NOT_FOUND)
        obj_instance=Safety.objects.get(pk=request.query_params['safety_id'])
        serializer = SafetySerializer(instance=obj_instance, data=request.data, partial=True)
        serializer=self.get_serializer(instance,data=request.data,partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.update(instance=instance,validated_data=(request.data))
        headers = self.get_success_headers(serializer.data)
        obj_instance=Safety.objects.get(pk=request.query_params['safety_id'])
        obj_instance.worker_watch="false"
        obj_instance.save()
        obj_instance=Safety.objects.get(pk=request.query_params['safety_id'])
        obj_instance.client_watch="false"
        obj_instance.save()
        instance=Safety.objects.get(pk=request.query_params['safety_id'])
        dicti={
                "id": instance.id,
                "project": {'id':instance.project.id,'name':instance.project.name,'created_date':instance.project.created_date.strftime("%Y-%m-%d %H:%M:%S" ) ,'status':instance.project.status, 'description':instance.project.description},
                "created_by":{'id':instance.created_by.id,'first_name':instance.created_by.first_name,'last_name':instance.created_by.last_name,'email':instance.created_by.email, 'phone':instance.created_by.phone,'profile_picture': instance.created_by.profile_picture},
                "name":instance.name,
                "description":instance.description,
                "file":instance.file,
                "type":instance.type,
                "created_date":instance.created_date.strftime("%Y-%m-%d %H:%M:%S" ),
                "updated_date":instance.updated_date.strftime("%Y-%m-%d %H:%M:%S" )}
        project=instance.project
        workers=ProjectWorker.objects.filter(project_id=instance.project.id)
        workers=[x.worker.id for x in workers]
        client=Project.objects.get(pk=project.id).client.id
        receivers=workers+[client]
        if instance.type=='safe_work_method_statement':
            for i in receivers:
                try:
                    notification_data={'title':'Safety Work Method Updated',
                    'sender_id':request.user.id,
                    'receiver_id':i,
                    'notification_type':"safety_work_method_updated",
                    'safety':instance.id,
                    'project':project.id,
                    'message':"Safety Work Method %s has been updated for %s project by %s %s"%(instance.name,Project.objects.get(pk=project.id).name,request.user.first_name,request.user.last_name)}  
                    notification=FCMSerializer(data=notification_data)
                    notification.is_valid(raise_exception=True)
                    notification.save()
                    data_object= {
                            "title": "Safety Work Method Updated",
                            "message":"Safety Work Method %s has been updated for %s project by %s %s"%(instance.name,Project.objects.get(pk=project.id).name,request.user.first_name,request.user.last_name),
                            "notification_type":"safety_work_method_updated",
                            "project_id":project.id,
                            "receiver_id":i,
                            "safety_work_method_id":instance.id,
                            "sender_id":request.user.id,
                            "fromNotification":True
                    }
                    send_notification_thread(User.objects.get(pk=notification_data.get("receiver_id")),data_object.get("title"),data_object.get("message"),data_object,len(FcmNotifications.objects.filter(receiver_id=notification_data.get("receiver_id"),watch="false")),request)
                except Exception as e:
                    print(e)
            return Response(dicti, status=status.HTTP_201_CREATED, headers=headers)
        elif instance.type=='material_safety_data_sheets':
            for i in receivers:
                try:
                    notification_data={'title':' Material Safety Updated ',
                    'sender_id':request.user.id,
                    'receiver_id':i,
                    'notification_type':"material_safety_updated",
                    'safety':instance.id,
                    'project':project.id,
                    'message':"Material safety %s has been updated for %s project by %s %s"%(instance.name,Project.objects.get(pk=project.id).name,request.user.first_name,request.user.last_name)}  
                    notification=FCMSerializer(data=notification_data)
                    notification.is_valid(raise_exception=True)
                    notification.save()
                    data_object= {
                            "title": " Material Safety Updated ",
                            "message":"Material safety %s has been updated for %s project by %s %s"%(instance.name,Project.objects.get(pk=project.id).name,request.user.first_name,request.user.last_name),
                            "notification_type":"material_safety_updated",
                            "project_id":project.id,
                            "receiver_id":i,
                            "material_safety_id":instance.id,
                            "sender_id":request.user.id,
                            "fromNotification":True
                    }
                    send_notification_thread(User.objects.get(pk=notification_data.get("receiver_id")),data_object.get("title"),data_object.get("message"),data_object,len(FcmNotifications.objects.filter(receiver_id=notification_data.get("receiver_id"),watch="false")),request)
                except Exception as e:
                    print(e)
            return Response(dicti, status=status.HTTP_201_CREATED, headers=headers)
        else:
            for i in receivers:
                try:
                    notification_data={'title':'  Work Health Updated ',
                    'sender_id':request.user.id,
                    'receiver_id':i,
                    'notification_type':"work_health_updated",
                    'safety':instance.id,
                    'project':project.id,
                    'message':"Work health %s has been updated for %s project by %s %s"%(instance.name,Project.objects.get(pk=project.id).name,request.user.first_name,request.user.last_name)}  
                    notification=FCMSerializer(data=notification_data)
                    notification.is_valid(raise_exception=True)
                    notification.save()
                    data_object= {
                            "title": " Work Health Updated ",
                            "message":"Work health %s has been updated for %s project by %s %s"%(instance.name,Project.objects.get(pk=project.id).name,request.user.first_name,request.user.last_name),
                            "notification_type":"work_health_updated",
                            "project_id":project.id,
                            "receiver_id":i,
                            "work_health_id":instance.id,
                            "sender_id":request.user.id,
                            "fromNotification":True
                    }
                    send_notification_thread(User.objects.get(pk=notification_data.get("receiver_id")),data_object.get("title"),data_object.get("message"),data_object,len(FcmNotifications.objects.filter(receiver_id=notification_data.get("receiver_id"),watch="false")),request)
                except Exception as e:
                    print(e)
            return Response(dicti, status=status.HTTP_201_CREATED, headers=headers)

class SiteRiskAssessmentQuestionsViewset(viewsets.GenericViewSet, mixins.CreateModelMixin, mixins.DestroyModelMixin,mixins.ListModelMixin,mixins.UpdateModelMixin):
    def get_permissions(self):
        if self.action == "create" :
            return [IsAuthenticated()]
        if self.action == "list":
            return [IsAuthenticated()]
        return [AllowAny()]
    queryset = SiteRiskAssessmentQuestions.objects.all()
    def get_serializer_class(self):
        if self.action == 'create' or self.action == "list":
            return SiteRiskAssessmentQuestionserializer
    def create(self, request, *args, **kwargs):
        request.data['created_by']=request.user.id
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data,status=status.HTTP_200_OK,headers=headers)
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

class IncidentTypeViewset(viewsets.GenericViewSet, mixins.CreateModelMixin, mixins.ListModelMixin,mixins.RetrieveModelMixin):
    serializer_class = IncidentTypeSerializer
    queryset = IncidentType.objects.all()
    def get_permissions(self):
        if self.action == "create":
            return [AllowAny()]            
        return [AllowAny()]

class IncidentReportViewset(viewsets.GenericViewSet, mixins.CreateModelMixin, mixins.DestroyModelMixin,mixins.ListModelMixin,mixins.UpdateModelMixin):
    def get_permissions(self):
        if self.action == "create" or self.action == "update_incident_report":
            return [IsAuthenticated()]
        if self.action == "list":
            return [IsAuthenticated()]
        return [AllowAny()]

    def get_queryset(self):
        if self.action == "update_incident_report" or self.action == "delete" or self.action=="create":
            if self.request.user.user_type=="builder":
                return IncidentReport.objects.filter(project__builder=self.request.user)
            if self.request.user.user_type=="worker" :
                return IncidentReport.objects.filter(created_by=self.request.user)
            if self.request.user.user_type=="client":
                return IncidentReport.objects.filter(project__client=self.request.user)
        if self.request.user.user_type=="builder":
            return IncidentReport.objects.filter(project__builder=self.request.user)
        if self.request.user.user_type=="client":
            return IncidentReport.objects.filter(project__client=self.request.user)
        if self.request.user.user_type=="worker":
            return IncidentReport.objects.filter(project__worker=self.request.user)
        
    def get_serializer_class(self):
        if self.action == 'create' or self.action == "update_incident_report":
            return IncidentReportSerializer
        if self.action == 'list':
            return IncidentReportListSerializer

    def create(self, request, *args, **kwargs):
        user=request.user
        if user.user_type=='worker'or user.user_type=='builder' or user.user_type=='client':
            try:
                    request.data['date_of_incident_reported'] = datetime.datetime.fromtimestamp(
                        int(request.data.get('date_of_incident_reported')))
                    request.data['date_of_incident'] = datetime.datetime.fromtimestamp(
                        int(request.data.get('date_of_incident')))
            except:
                    request.data['date_of_incident_reported'] = datetime.datetime.fromtimestamp(
                        int(request.data.get('date_of_incident_reported'))/1000)
                    request.data['date_of_incident'] = datetime.datetime.fromtimestamp(
                        int(request.data.get('date_of_incident'))/1000)
            request.data['date_of_incident_reported'] = request.data['date_of_incident_reported'].date()
            request.data['date_of_incident'] = request.data['date_of_incident'].date()
            data = request.data
            data["created_by"]=request.user.id
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            instance=IncidentReport.objects.get(pk=serializer.data.get('id'))
            project=IncidentReport.objects.get(pk=serializer.data.get('id')).project
            person_completing_form=IncidentReport.objects.get(pk=serializer.data.get('id')).person_completing_form
            witness_of_incident=IncidentReport.objects.get(pk=serializer.data.get('id')).witness_of_incident
            receivers=[]
            if witness_of_incident != None:
                if person_completing_form.id==witness_of_incident.id:
                    receivers=[person_completing_form.id]
                else:
                    receivers=[person_completing_form.id]+[witness_of_incident.id]
                for i in receivers:
                    try:
                        notification_data={'title':' Incident Report Added',
                        'sender_id':request.user.id,
                        'receiver_id':i,
                        'notification_type':"new_incident_report_created",
                        'incident_report':instance.id,
                        'project':project.id,
                        'message':"A new Incident Report has been created for %s project by %s %s"%(Project.objects.get(pk=project.id).name,request.user.first_name,request.user.last_name)}  
                        notification=FCMSerializer(data=notification_data)
                        notification.is_valid(raise_exception=True)
                        notification.save()
                        data_object= {
                                "title": " Incident Report Added",
                                "message":"A new Incident Report has been created for %s project by %s %s"%(Project.objects.get(pk=project.id).name,request.user.first_name,request.user.last_name),
                                "notification_type":"new_incident_report_created",
                                "project_id":project.id,
                                "receiver_id":i,
                                "sender_id":request.user.id,
                                "incident_report_id":instance.id,
                                "fromNotification":True
                        }
                        send_notification_thread(User.objects.get(pk=notification_data.get("receiver_id")),data_object.get("title"),data_object.get("message"),data_object,len(FcmNotifications.objects.filter(receiver_id=notification_data.get("receiver_id"),watch="false")),request)
                    except Exception as e:
                        print(e)
                return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
            else:
                receivers=[person_completing_form.id]
                for i in receivers:
                    try:
                        notification_data={'title':' Incident Report Added',
                        'sender_id':request.user.id,
                        'receiver_id':i,
                        'notification_type':"new_incident_report_created",
                        'incident_report':instance.id,
                        'project':project.id,
                        'message':"A new Incident Report has been created for %s project by %s %s"%(Project.objects.get(pk=project.id).name,request.user.first_name,request.user.last_name)}  
                        notification=FCMSerializer(data=notification_data)
                        notification.is_valid(raise_exception=True)
                        notification.save()
                        data_object= {
                                "title": " Incident Report Added",
                                "message":"A new Incident Report has been created for %s project by %s %s"%(Project.objects.get(pk=project.id).name,request.user.first_name,request.user.last_name),
                                "notification_type":"new_incident_report_created",
                                "project_id":project.id,
                                "receiver_id":i,
                                "sender_id":request.user.id,
                                "incident_report_id":instance.id,
                                "fromNotification":True
                        }
                        send_notification_thread(User.objects.get(pk=notification_data.get("receiver_id")),data_object.get("title"),data_object.get("message"),data_object,len(FcmNotifications.objects.filter(receiver_id=notification_data.get("receiver_id"),watch="false")),request)
                    except Exception as e:
                        print(e)
                return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


    @action(methods=['PUT'],detail=False,url_path='update',url_name='update_incident_report')
    def update_incident_report(self, request,*args, **kwargs):
        data=request.data
        if request.query_params.get('incident_report_id'):
            try:
                instance = self.get_queryset().get(
                    pk=request.query_params['incident_report_id'])
            except:
                return Response('Not found.', status=status.HTTP_404_NOT_FOUND)
        else:
            return Response('Please specify a incident_report_id.', status=status.HTTP_404_NOT_FOUND)
        if 'date_of_incident_reported' in data:     
            try:
                request.data['date_of_incident_reported'] = datetime.datetime.fromtimestamp(
                    int(request.data.get('date_of_incident_reported')))

            except:
                request.data['date_of_incident_reported'] = datetime.datetime.fromtimestamp(
                    int(request.data.get('date_of_incident_reported'))/1000)
            request.data['date_of_incident_reported'] = request.data['date_of_incident_reported'].date()
        if 'date_of_incident' in data:     
            try:
                request.data['date_of_incident'] = datetime.datetime.fromtimestamp(
                    int(request.data.get('date_of_incident')))
            except:

                request.data['date_of_incident'] = datetime.datetime.fromtimestamp(
                    int(request.data.get('date_of_incident'))/1000)

            request.data['date_of_incident'] = request.data['date_of_incident'].date()
        obj_instance=IncidentReport.objects.get(pk=request.query_params['incident_report_id'])
        serializer = IncidentReportSerializer(instance=obj_instance, data=request.data, partial=True)
        serializer=self.get_serializer(instance,data=request.data,partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.update(instance=instance,validated_data=(request.data))
        headers = self.get_success_headers(serializer.data)
        obj_instance=IncidentReport.objects.get(pk=request.query_params['incident_report_id'])
        obj_instance.person_completing_form_watch="false"
        obj_instance.save()
        obj_instance=IncidentReport.objects.get(pk=request.query_params['incident_report_id'])
        obj_instance.witness_of_incident_watch="false"
        obj_instance.save()
        result=serializer.data
        instance=IncidentReport.objects.get(pk=request.query_params['incident_report_id'])
        result['created_by']= {'id':instance.created_by.id,'first_name':instance.created_by.first_name,'last_name':instance.created_by.last_name,'phone':instance.created_by.phone,'email':instance.created_by.email,'profile_picture':instance.created_by.profile_picture}
        result['person_completing_form'] ={'id':instance.person_completing_form.id,'first_name':instance.person_completing_form.first_name,'last_name':instance.person_completing_form.last_name,'phone':instance.person_completing_form.phone,'email':instance.person_completing_form.email,'profile_picture':instance.person_completing_form.profile_picture}
        result['witness_of_incident'] ={'id':instance.witness_of_incident.id,'first_name':instance.witness_of_incident.first_name,'last_name':instance.witness_of_incident.last_name,'phone':instance.witness_of_incident.phone,'email':instance.witness_of_incident.email,'profile_picture':instance.witness_of_incident.profile_picture}
        result['project']={'id':instance.project.id,'name':instance.project.name,'created_date':instance.project.created_date.strftime("%Y-%m-%d %H:%M:%S" ) ,'status':instance.project.status, 'description':instance.project.description},
        result['type_of_incident']={'id':instance.type_of_incident.id,'name':instance.type_of_incident.name}
        project=IncidentReport.objects.get(pk=serializer.data.get('id')).project
        person_completing_form=IncidentReport.objects.get(pk=serializer.data.get('id')).person_completing_form
        witness_of_incident=IncidentReport.objects.get(pk=serializer.data.get('id')).witness_of_incident
        receivers=[]
        if person_completing_form.id==witness_of_incident.id:
            receivers=[person_completing_form.id]
        else:
            receivers=[person_completing_form.id]+[witness_of_incident.id]
        for i in receivers:
            try:
                notification_data={'title':' Incident Report Updated',
                'sender_id':request.user.id,
                'receiver_id':i,
                'notification_type':"incident_report_updated",
                'incident_report':instance.id,
                'project':project.id,
                'message':"Incident Report %s has been updated for %s project by %s %s"%(instance.name,Project.objects.get(pk=project.id).name,request.user.first_name,request.user.last_name)}  
                notification=FCMSerializer(data=notification_data)
                notification.is_valid(raise_exception=True)
                notification.save()
                data_object= {
                        "title": " Incident Report Updated",
                        "message":"Incident Report %s has been updated for %s project by %s %s"%(instance.name,Project.objects.get(pk=project.id).name,request.user.first_name,request.user.last_name),
                        "notification_type":"incident_report_updated",
                        "project_id":project.id,
                        "receiver_id":i,
                        "sender_id":request.user.id,
                        "incident_report_id":instance.id,
                        "fromNotification":True
                }
                send_notification_thread(User.objects.get(pk=notification_data.get("receiver_id")),data_object.get("title"),data_object.get("message"),data_object,len(FcmNotifications.objects.filter(receiver_id=notification_data.get("receiver_id"),watch="false")),request)
            except Exception as e:
                print(e)
        return Response(result,status=status.HTTP_200_OK,headers=headers)

    @action(methods=['delete'], detail=True, url_path="")
    def delete(self, request, *args, **kwargs):
        if request.query_params.get('incident_report_id'):
            project=IncidentReport.objects.get(id=request.query_params.get('incident_report_id')).project
            if self.request.user==IncidentReport.objects.get(pk=request.query_params.get('incident_report_id')).created_by or self.request.user==Project.objects.get(id=project.id).builder or self.request.user==Project.objects.get(id=project.id).client:
                instance = IncidentReport.objects.get(pk=request.query_params.get('incident_report_id'))
                project=instance.project
                person_completing_form=instance.person_completing_form
                witness_of_incident=instance.witness_of_incident
                receivers=[]
                if person_completing_form.id==witness_of_incident.id:
                    receivers=[person_completing_form.id]
                else:
                    receivers=[person_completing_form.id]+[witness_of_incident.id]
                for i in receivers:
                    try:
                        notification_data={'title':' Incident Report Deleted',
                        'sender_id':request.user.id,
                        'receiver_id':i,
                        'notification_type':"incident_report_deleted",
                        'project':project.id,
                        'message':"Incident Report %s has been deleted for %s project by %s %s"%(instance.name,Project.objects.get(pk=project.id).name,request.user.first_name,request.user.last_name)}  
                        notification=FCMSerializer(data=notification_data)
                        notification.is_valid(raise_exception=True)
                        notification.save()
                        data_object= {
                                "title": " Incident Report Deleted",
                                "message":"Incident Report %s has been deleted for %s project by %s %s"%(instance.name,Project.objects.get(pk=project.id).name,request.user.first_name,request.user.last_name),
                                "notification_type":"incident_report_deleted",
                                "project_id":project.id,
                                "receiver_id":i,
                                "sender_id":request.user.id,
                                "fromNotification":True
                        }
                        send_notification_thread(User.objects.get(pk=notification_data.get("receiver_id")),data_object.get("title"),data_object.get("message"),data_object,len(FcmNotifications.objects.filter(receiver_id=notification_data.get("receiver_id"),watch="false")),request)
                    except Exception as e:
                        print(e)
                instance = IncidentReport.objects.get(pk=request.query_params.get('incident_report_id')).delete()
                return Response(data="IncidentReport  Deleted Successfully", status=status.HTTP_200_OK)
            else: 
                return Response('You dont have the access to delete this Safety.', status=status.HTTP_404_NOT_FOUND)
        return Response('Please specify a Safety ID.', status=status.HTTP_404_NOT_FOUND)

    def list(self, request, *args, **kwargs):
        if self.filter_queryset(self.get_queryset())==None:
            queryset =IncidentReport.objects.filter(project=request.query_params['project_id']).order_by('-created_date')
        else:
            queryset = self.filter_queryset(
                self.get_queryset()).order_by('-report_created_date')
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

class SiteRiskAssessmentViewset(viewsets.GenericViewSet, mixins.CreateModelMixin, mixins.DestroyModelMixin,mixins.ListModelMixin,mixins.UpdateModelMixin):
    def get_permissions(self):
        if self.action == "create" or self.action == "update_site_risk_assessment":
            return [IsAuthenticated()]
        if self.action == "list":
            return [IsAuthenticated()]
        return [AllowAny()]

    def get_queryset(self):
        if  self.action == "delete" or self.action=="create":
            if self.request.user.user_type=="builder":
                return SiteRiskAssessment.objects.filter(project__builder=self.request.user)
            if self.request.user.user_type=="worker" :
                return SiteRiskAssessment.objects.filter(created_by=self.request.user)
            if self.request.user.user_type=="client":
                return SiteRiskAssessment.objects.filter(project__client=self.request.user)
        if self.request.user.user_type=="builder":
            return SiteRiskAssessment.objects.filter(project__builder=self.request.user)
        if self.request.user.user_type=="client":
            return SiteRiskAssessment.objects.filter(project__client=self.request.user)
        if self.request.user.user_type=="worker":
            return SiteRiskAssessment.objects.filter(project__worker=self.request.user)
        if self.request.user.user_type=="worker" :
                return SiteRiskAssessment.objects.filter(created_by=self.request.user)
        
    def get_serializer_class(self):
        if self.action == 'create' or self.action == "submit_response":
            return SiteRiskAssessmentSerializer
        if self.action == 'list':
            return SiteRiskAssessmentListSerializer

    def create(self, request, *args, **kwargs):
        user=request.user
        result=[]
        list_of_ids=[]
        receivers=[]
        create_data={}
        site_risk_assessment_relation_through_data={}
        if user.user_type=='worker'or user.user_type=='builder' or user.user_type=='client':
            if request.data:
                for i in request.data:    
                    data = request.data
                    i["created_by"]=request.user.id
                    serializer = self.get_serializer(data=i)
                    serializer.is_valid(raise_exception=True)
                    self.perform_create(serializer)
                    headers = self.get_success_headers(serializer.data)
                    list_of_ids.append(serializer.data.get('id'))
                create_data["created_by"]=request.user.id
                create_data["site_risk_assessment_list"]=list_of_ids
                site_risk_assessment_relation = SiteRiskAssessmentRelationSerializer(data=create_data)
                site_risk_assessment_relation.is_valid(raise_exception=True)
                site_risk_assessment_relation.save()
                print(list_of_ids)
                for i in list_of_ids:    
                    instance=SiteRiskAssessment.objects.get(pk=i)
                    # site_risk_assessment_relation_through= SiteRiskAssessmentRelation.objects.get(pk=site_risk_assessment_relation.data.get('id')) 
                    site_risk_assessment_relation_through_data['project']=instance.project.id
                    site_risk_assessment_relation_through_data['siteriskassessmentrelation']=site_risk_assessment_relation.data.get('id')
                    site_risk_assessment_relation_through_data['siteriskassessment']=i
                    site_risk_assessment_list = SiteRiskAssessmentThroughSerializer(data=site_risk_assessment_relation_through_data)
                    site_risk_assessment_list.is_valid(raise_exception=True)
                    site_risk_assessment_list.save()
                for i in list_of_ids:
                    instance=SiteRiskAssessment.objects.get(pk=i)
                    if instance.assigned_to != None:
                        dicti={
                            "id": instance.id,
                            "project": {'id':instance.project.id,'name':instance.project.name,'created_date':instance.project.created_date.strftime("%Y-%m-%d %H:%M:%S" ) ,'status':instance.project.status, 'description':instance.project.description},
                            "created_by":{'id':instance.created_by.id,'first_name':instance.created_by.first_name,'last_name':instance.created_by.last_name,'email':instance.created_by.email, 'phone':instance.created_by.phone,'profile_picture': instance.created_by.profile_picture},
                            "assigned_to":{'id':instance.assigned_to.id ,'first_name':instance.assigned_to.first_name,'last_name':instance.assigned_to.last_name,'email':instance.assigned_to.email, 'phone':instance.assigned_to.phone,'profile_picture': instance.assigned_to.profile_picture },
                            "file":instance.file,
                            "upload_file":instance.upload_file,
                            "response":instance.response,
                            "question":{"id":instance.question.id,"question":instance.question.question},
                            "created_date":instance.created_date.strftime("%Y-%m-%d %H:%M:%S" ),
                            "updated_date":instance.updated_date.strftime("%Y-%m-%d %H:%M:%S" )}
                        project=instance.project
                        assigned_to=instance.assigned_to
                        receivers=[assigned_to.id]
                    else: 
                        dicti={
                            "id": instance.id,
                            "project": {'id':instance.project.id,'name':instance.project.name,'created_date':instance.project.created_date.strftime("%Y-%m-%d %H:%M:%S" ) ,'status':instance.project.status, 'description':instance.project.description},
                            "created_by":{'id':instance.created_by.id,'first_name':instance.created_by.first_name,'last_name':instance.created_by.last_name,'email':instance.created_by.email, 'phone':instance.created_by.phone,'profile_picture': instance.created_by.profile_picture},                            "file":instance.file,
                            "response":instance.response,
                            "upload_file":instance.upload_file,
                            "assigned_to":{},
                            "question":{"id":instance.question.id,"question":instance.question.question},
                            "created_date":instance.created_date.strftime("%Y-%m-%d %H:%M:%S" ),
                            "updated_date":instance.updated_date.strftime("%Y-%m-%d %H:%M:%S" )}
                    result.append(dicti)
                if receivers!=[]:
                    for j in receivers:
                        try:
                            notification_data={'title':'  Site Risk Added',
                            'sender_id':request.user.id,
                            'receiver_id':j,
                            'notification_type':"new_site_risk_created",
                            'project':project.id,
                            'site_risk_id':i,
                            'message':"A new site risk has been created for %s project by %s %s"%(Project.objects.get(pk=project.id).name,request.user.first_name,request.user.last_name)}  
                            notification=FCMSerializer(data=notification_data)
                            notification.is_valid(raise_exception=True)
                            notification.save()
                            data_object= {
                                    "title": "  Site Risk Added",
                                    "message":"A new site risk has been created for %s project by %s %s"%(Project.objects.get(pk=project.id).name,request.user.first_name,request.user.last_name),
                                    "notification_type":"new_site_risk_created",
                                    "project_id":project.id,
                                    "receiver_id":j,
                                    "sender_id":request.user.id,
                                    "site_risk_id":i,
                                    "fromNotification":True
                            }
                            send_notification_thread(User.objects.get(pk=notification_data.get("receiver_id")),data_object.get("title"),data_object.get("message"),data_object,len(FcmNotifications.objects.filter(receiver_id=notification_data.get("receiver_id"),watch="false")),request)
                        except Exception as e:
                            print(e)
                    return Response(data=result,status=status.HTTP_200_OK,headers=headers)
                else:
                    return Response(data=result,status=status.HTTP_200_OK,headers=headers)
        else:
            return Response('Incomplete Data', status=status.HTTP_404_NOT_FOUND)
                       
    def list(self, request, *args, **kwargs):
        if self.filter_queryset(self.get_queryset())==None:
            queryset =SiteRiskAssessment.objects.filter(project=request.query_params['project_id']).order_by('-created_date')
        else:
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

    @action(methods=['PUT'],detail=False,url_path='response',url_name='submit_response')
    def submit_response(self, request,*args, **kwargs):
        result=[]
        if request.data:
            try:
                instance =SiteRiskAssessment.objects.get(pk=request.data.get('id'))
            except:
                return Response('Not found.', status=status.HTTP_404_NOT_FOUND)
            update_data={'response':request.data.get('response'),'upload_file':request.data.get('upload_file')}
            serializer = SiteRiskAssessmentSerializer(instance=instance, data= update_data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.update(instance=instance,validated_data=update_data)
            headers = self.get_success_headers(serializer.data)
            obj_instance =SiteRiskAssessment.objects.get(pk=request.data.get('id'))
            obj_instance.builder_watch="false"
            obj_instance.save()
            project=instance.project
            created_by=instance.created_by
            assigned_to=instance.assigned_to
            receivers=[created_by.id]
            for j in receivers:
                try:
                    notification_data={'title':'  Site Risk Response Submitted',
                    'sender_id':request.user.id,
                    'receiver_id':j,
                    'notification_type':"site_risk_response_submitted",
                    'project':project.id,
                    'site_risk_id':instance.id,
                    'message':"Site Risk Response has been Submitted for %s project by %s %s"%(Project.objects.get(pk=project.id).name,request.user.first_name,request.user.last_name)}  
                    notification=FCMSerializer(data=notification_data)
                    notification.is_valid(raise_exception=True)
                    notification.save()
                    data_object= {
                            "title": "  Site Risk Response Submitted",
                            "message":"Site Risk Response has been Submitted for %s project by %s %s"%(Project.objects.get(pk=project.id).name,request.user.first_name,request.user.last_name),
                            "notification_type":"site_risk_response_submitted",
                            "project_id":project.id,
                            "receiver_id":j,
                            "sender_id":request.user.id,
                            "site_risk_id":instance.id,
                            "fromNotification":True
                    }
                    send_notification_thread(User.objects.get(pk=notification_data.get("receiver_id")),data_object.get("title"),data_object.get("message"),data_object,len(FcmNotifications.objects.filter(receiver_id=notification_data.get("receiver_id"),watch="false")),request)
                except Exception as e:
                    print(e)
            return Response(data=serializer.data,status=status.HTTP_200_OK,headers=headers)
        else:
            return Response(data='Invalid/Incomplete data', status=status.HTTP_400_BAD_REQUEST)

class SiteRiskAssessmentRelationViewset(viewsets.GenericViewSet, mixins.CreateModelMixin, mixins.DestroyModelMixin,mixins.ListModelMixin,mixins.UpdateModelMixin):
    
    def get_permissions(self):
        if self.action == "list":
            return [IsAuthenticated()]
        return [AllowAny()]

    def get_queryset(self):
        if self.request.user.user_type=="builder":
            return SiteRiskAssessmentRelation.objects.filter(siteriskassessmentthrough__project__id =self.request.query_params.get('project_id')).distinct()
        if self.request.user.user_type=="client":
            return SiteRiskAssessmentRelation.objects.filter(siteriskassessmentthrough__project__id=self.request.query_params.get('project_id')).distinct()
        if self.request.user.user_type=="worker":
            return SiteRiskAssessmentRelation.objects.filter(siteriskassessmentthrough__project__id=self.request.query_params.get('project_id')).distinct()
        if self.request.user:
            return SiteRiskAssessmentRelation.objects.filter(created_by=self.request.user).distinct()
           
        
    def get_serializer_class(self):
        if self.action == 'list':
            return SiteRiskAssessmentRelationListSerializer
    
    def list(self, request, *args, **kwargs):
        if request.query_params.get('project_id'):
            queryset = self.filter_queryset(
                    self.get_queryset()).order_by('-created_date')
        else:
            return Response(data='Please Specify project_id', status=status.HTTP_400_BAD_REQUEST)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

class VariationsViewset(viewsets.GenericViewSet, mixins.CreateModelMixin, mixins.ListModelMixin,mixins.RetrieveModelMixin):
    def get_permissions(self):
        if self.action == "create" or self.action=='list'or self.action=='retrieve':
            return [IsAuthenticated()]
        return [AllowAny()]

    def get_queryset(self):
        if self.action=='retrieve':
            try:
                if not Variations.objects.get(project__builder=self.request.user) and Variations.objects.get(project__client=self.request.user) and Variations.objects.get(project__worker=self.request.user):
                    return User.objects.filter(pk=self.request.user.id)
            except:
                if self.request.user.user_type=="builder":
                    return Variations.objects.filter(project__builder=self.request.user)
                if self.request.user.user_type=="client":
                    return Variations.objects.filter(project__client=self.request.user)
                if self.request.user.user_type=="worker":
                    return Variations.objects.filter(project__worker=self.request.user)
        if self.action=="accept" or self.action=="reject" or self.action=="create": 
            if self.request.user.user_type=="builder":
                return Variations.objects.filter(project__builder=self.request.user)
            if self.request.user.user_type=="client":
                return Variations.objects.filter(project__client=self.request.user)
            if self.request.user.user_type=="worker":
                return Variations.objects.filter(project__worker=self.request.user)
        if self.action=="list":
            if self.request.user:
                return (Variations.objects.filter(sender=self.request.user)|(Variations.objects.filter(receiver=self.request.user))|(Variations.objects.filter(created_by=self.request.user))).distinct()

        if self.action == 'update_variation' :
            if self.request.user.user_type=="builder":
                    return Variations.objects.filter(project__builder=self.request.user)
            else:
                    return Variations.objects.filter(sender=self.request.user)

    def get_serializer_class(self):
        if self.action == 'create' or self.action == 'update_variation':
            return VariationsSerializer
        if self.action=='list':
            return VariationsListSerializer
        if self.action=='retrieve':
            try:
                if Variations.objects.get(pk=self.request.query_params.get('variation_id')).sender.id==self.request.user.id:
                    return VariationsDetailsSenderSerializer
                if VariationReceiver.objects.get(variation=self.request.query_params.get('variation_id'),receiver=self.request.user.id).receiver.id==self.request.user.id:
                    return VariationsDetailsReceiverSerializer
            except:
               return VariationsDetailsNonUserSerializer


    def create(self, request, *args, **kwargs):
        if request.data['receiver']:
            receiver=request.data['receiver']
            request.data["created_by"]=request.user.id
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
        else:
            return Response(data='Invalid/Incomplete data', status=status.HTTP_400_BAD_REQUEST)
        for i in receiver:    
            variation= Variations.objects.get(pk=serializer.data.get('id')) 
            receiver = i
            variation.receiver.add(receiver)
            variation.save()
        instance = self.get_queryset().get(pk=serializer.data.get('id'))
        serializer = VariationsSerializer(instance)
        headers = self.get_success_headers(serializer.data)
        receivers=request.data['receiver']
        for i in receivers:
            try:
                notification_data={'title':'New Variation Added',
                'sender_id':serializer.data.get('sender'),
                'receiver_id':i,
                'project':serializer.data.get('project'),
                'variation':serializer.data.get('id'),
                'notification_type':"new_variation_created",
                'message':"A new variation has been created for %s project by %s %s"%(Project.objects.get(pk=serializer.data.get('project')).name,Variations.objects.get(pk=serializer.data.get('id')).sender.first_name,Variations.objects.get(pk=serializer.data.get('id')).sender.last_name)}  
                notification=FCMSerializer(data=notification_data)
                notification.is_valid(raise_exception=True)
                notification.save()
                data_object= {
                        "title": "New Variation Added",
                        "message": "A new variation has been created for %s project by %s %s"%(Project.objects.get(pk=serializer.data.get('project')).name,Variations.objects.get(pk=serializer.data.get('id')).sender.first_name,Variations.objects.get(pk=serializer.data.get('id')).sender.last_name),
                        "notification_type":"new_variation_created",
                        "project_id":serializer.data.get('project'),
                        "receiver_id":i,
                        "sender_id":request.user.id,
                        "variation_id":serializer.data.get('id'),
                        "fromNotification":True
                }
                send_notification_thread(User.objects.get(pk=notification_data.get("receiver_id")),data_object.get("title"),data_object.get("message"),data_object,len(FcmNotifications.objects.filter(receiver_id=notification_data.get("receiver_id"),watch="false")),request)
            except Exception as e:
                print(e)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def retrieve(self, request, *args, **kwargs):
        if request.query_params.get('variation_id'):
            try:
                instance = self.get_queryset().get(
                    pk=request.query_params['variation_id'])
            except:
                instance=Variations.objects.get(
                    pk=request.query_params['variation_id'])
        else:
            return Response('Please specify a variation ID.', status=status.HTTP_404_NOT_FOUND)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(methods=['delete'], detail=True, url_path="")
    def delete(self, request, *args, **kwargs):
        if request.query_params.get('variation_id'):
            project=Variations.objects.get(id=request.query_params.get('variation_id')).project
            if self.request.user==Variations.objects.get(pk=request.query_params.get('variation_id')).sender or self.request.user==Project.objects.get(id=project.id).builder:
                sender=Variations.objects.get(pk=request.query_params.get('variation_id')).sender
                receivers=VariationReceiver.objects.filter(variation=Variations.objects.get(pk=request.query_params.get('variation_id')))
                receivers=[x.receiver for x in receivers]
                for i in receivers:
                    try:
                        notification_data={'title':'Variation Deleted',
                        'sender_id':request.user.id,
                        'receiver_id':i.id,
                        'notification_type':"variation_deleted",
                        'message':" Variation %s has been deleted by %s %s"%(Variations.objects.get(pk=request.query_params.get('variation_id')).name,request.user.first_name,request.user.last_name)}  
                        notification=FCMSerializer(data=notification_data)
                        notification.is_valid(raise_exception=True)
                        notification.save()
                        data_object= {
                                "title": "Variation Deleted",
                                "message":" Variation %s has been deleted by %s %s"%(Variations.objects.get(pk=request.query_params.get('variation_id')).name,request.user.first_name,request.user.last_name),
                                "notification_type":"variation_deleted",
                                "project_id":project.id,
                                "receiver_id":i.id,
                                "sender_id":request.user.id,
                                "fromNotification":True
                        }
                        send_notification_thread(User.objects.get(pk=notification_data.get("receiver_id")),data_object.get("title"),data_object.get("message"),data_object,len(FcmNotifications.objects.filter(receiver_id=notification_data.get("receiver_id"),watch="false")),request)
                    except Exception as e:
                        print(e)
                obj=VariationReceiver.objects.filter(
                    variation=Variations.objects.get(
                    pk=request.query_params.get('variation_id'))).delete()
                instance = Variations.objects.get(
                    pk=request.query_params.get('variation_id')).delete()
                return Response(data="Variation Deleted Successfully", status=status.HTTP_200_OK)
            else: 
                return Response('You dont have the access to delete this variation only sender can delete this variation.', status=status.HTTP_404_NOT_FOUND)
        return Response('Please specify a variation ID.', status=status.HTTP_404_NOT_FOUND)

    @action(methods=['PUT'],detail=False,url_path='update',url_name='update_variation')
    def update_variation(self, request,*args, **kwargs):
        if request.query_params.get('variation_id'):
            try:
                instance = self.get_queryset().get(
                    pk=request.query_params['variation_id'])
            except:
                return Response('Not found.', status=status.HTTP_404_NOT_FOUND)
        else:
            return Response('Please specify a variation_id.', status=status.HTTP_404_NOT_FOUND)
        obj_instance=Variations.objects.get(pk=request.query_params['variation_id'])
        serializer = VariationsSerializer(instance=obj_instance, data=request.data, partial=True)
        serializer=self.get_serializer(instance,data=request.data,partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.update(instance=instance,validated_data=(request.data))
        headers = self.get_success_headers(serializer.data)
        sender=Variations.objects.get(pk=request.query_params.get('variation_id')).sender
        receivers=VariationReceiver.objects.filter(variation=Variations.objects.get(pk=request.query_params.get('variation_id')))
        for i in receivers:
            i.receiver_watch="false"
            i.save()
        receivers=[x.receiver for x in receivers]
        for i in receivers:
            try:
                notification_data={'title':'Variation Updated',
                'sender_id':request.user.id,
                'receiver_id':i.id,
                'project':serializer.data.get('project'),
                'variation':serializer.data.get('id'),
                'notification_type':"variation_updated",
                'message':"Variation has been updated for %s project by %s %s"%(Project.objects.get(pk=serializer.data.get('project')).name,request.user.first_name,request.user.last_name)}  
                notification=FCMSerializer(data=notification_data)
                notification.is_valid(raise_exception=True)
                notification.save()
                data_object= {
                        "title": "Variation Updated",
                        "message":"Variation has been updated for %s project by %s %s"%(Project.objects.get(pk=serializer.data.get('project')).name,request.user.first_name,request.user.last_name),
                        "notification_type":"variation_updated",
                        "project_id":serializer.data.get('project'),
                        "receiver_id":i.id,
                        "sender_id":request.user.id,
                        "variation_id":serializer.data.get('id'),
                        "fromNotification":True
                }
                send_notification_thread(User.objects.get(pk=notification_data.get("receiver_id")),data_object.get("title"),data_object.get("message"),data_object,len(FcmNotifications.objects.filter(receiver_id=notification_data.get("receiver_id"),watch="false")),request)
            except Exception as e:
                print(e)
        return Response(serializer.data,status=status.HTTP_200_OK,headers=headers)
    
    @action(methods=['GET'],detail=False,url_path='accept',url_name='accept_variation')
    def accept(self, request, *args, **kwargs):
        q = request.query_params
        if not q.get('variation_id') :
            return Response(data='Invalid/Incomplete data', status=status.HTTP_400_BAD_REQUEST)
        obj = VariationReceiver.objects.get(variation=q.get('variation_id'),receiver=request.user)
        obj.action = 'accepted'
        obj.save()
        obj2=Variations.objects.get(pk=q.get('variation_id'))
        obj2.sender_watch = 'false'
        obj2.save()
        try:
            notification_data={'title':'Variation Accepted',
            'sender_id':self.request.user.id,
            'receiver_id':Variations.objects.get(pk=q.get('variation_id')).sender.id,
            'notification_type':"variation_accepted",
            'project':Variations.objects.get(pk=q.get('variation_id')).project.id,
            'variation':Variations.objects.get(pk=q.get('variation_id')).id,
            'message':"Variation has been accepted by %s %s for %s project."%(request.user.first_name,request.user.last_name,Variations.objects.get(pk=q.get('variation_id')).project.name)}  
            notification=FCMSerializer(data=notification_data)
            notification.is_valid(raise_exception=True)
            notification.save()
            data_object= {
                    "title": "Variation Accepted",
                    "message":"Variation has been accepted by %s %s for %s project."%(request.user.first_name,request.user.last_name,Variations.objects.get(pk=q.get('variation_id')).project.name), 
                    "notification_type":"variation_accepted",
                    "project_id":Variations.objects.get(pk=q.get('variation_id')).project.id,
                    "receiver_id":Variations.objects.get(pk=q.get('variation_id')).sender.id,
                    "variation_id":Variations.objects.get(pk=q.get('variation_id')).id,
                    "sender_id":request.user.id,
                    "fromNotification":True
            }
            send_notification_thread(User.objects.get(pk=notification_data.get("receiver_id")),data_object.get("title"),data_object.get("message"),data_object,len(FcmNotifications.objects.filter(receiver_id=notification_data.get("receiver_id"),watch="false")),request)
            return Response(data='Variation Accepted.', status=status.HTTP_200_OK)
        except Exception as e:
            print(e)
            return Response(data='Variation Accepted.', status=status.HTTP_200_OK)
    
    @action(methods=['GET'],detail=False,url_path='reject',url_name='reject_variation')
    def reject(self, request, *args, **kwargs):
        q = request.query_params
        if not q.get('variation_id') :
            return Response(data='Invalid/Incomplete data', status=status.HTTP_400_BAD_REQUEST)
        obj = VariationReceiver.objects.get(variation=q.get('variation_id'),receiver=request.user)
        obj.action = 'rejected'
        obj.save()
        obj2=Variations.objects.get(pk=q.get('variation_id'))
        obj2.sender_watch = 'false'
        obj2.save()
        try:
            notification_data={'title':'Variation Rejected',
            'sender_id':self.request.user.id,
            'receiver_id':Variations.objects.get(pk=q.get('variation_id')).sender.id,
            'notification_type':"variation_rejected",
            'project':Variations.objects.get(pk=q.get('variation_id')).project.id,
            'variation':Variations.objects.get(pk=q.get('variation_id')).id,
            'message':"Variation has been rejected by %s %s for %s project."%(request.user.first_name,request.user.last_name,Variations.objects.get(pk=q.get('variation_id')).project.name)}  
            notification=FCMSerializer(data=notification_data)
            notification.is_valid(raise_exception=True)
            notification.save()
            data_object= {
                    "title": "Variation Rejected",
                    "message":"Variation has been rejected by %s %s for %s project."%(request.user.first_name,request.user.last_name,Variations.objects.get(pk=q.get('variation_id')).project.name), 
                    "notification_type":"variation_rejected",
                    "project_id":Variations.objects.get(pk=q.get('variation_id')).project.id,
                    "receiver_id":Variations.objects.get(pk=q.get('variation_id')).sender.id,
                    "variation_id":Variations.objects.get(pk=q.get('variation_id')).id,
                    "sender_id":request.user.id,
                    "fromNotification":True
            }
            send_notification_thread(User.objects.get(pk=notification_data.get("receiver_id")),data_object.get("title"),data_object.get("message"),data_object,len(FcmNotifications.objects.filter(receiver_id=notification_data.get("receiver_id"),watch="false")),request)
            return Response(data='Variation Rejected.', status=status.HTTP_200_OK)
        except Exception as e:
            print(e)
            return Response(data='Variation Rejected.', status=status.HTTP_200_OK)

    def list(self, request, *args, **kwargs):
        if self.filter_queryset(self.get_queryset())==None:
            queryset =Variations.objects.filter(project=request.query_params['project_id']).order_by('-created_date')   
        else:
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

class EOTViewset(viewsets.GenericViewSet, mixins.CreateModelMixin, mixins.ListModelMixin,mixins.RetrieveModelMixin):
    def get_permissions(self):
        if self.action == "create" or self.action=='list'or self.action=='retrieve' or self.action=='update_eot':
            return [IsAuthenticated()]
        return [AllowAny()]

    def get_queryset(self):
        if self.action=='retrieve':
            try:
                if not EOT.objects.get(project__builder=self.request.user) and EOT.objects.get(project__client=self.request.user) and EOT.objects.get(project__worker=self.request.user):
                    return User.objects.filter(pk=self.request.user.id)
            except:
                if self.request.user.user_type=="builder":
                    return EOT.objects.filter(project__builder=self.request.user)
                if self.request.user.user_type=="client":
                    return EOT.objects.filter(project__client=self.request.user)
                if self.request.user.user_type=="worker":
                    return EOT.objects.filter(project__worker=self.request.user)
        if self.action=="accept" or self.action=="create" or self.action=='list':
            if self.request.user.user_type=="builder":
                return EOT.objects.filter(project__builder=self.request.user)
            if self.request.user.user_type=="client":
                return EOT.objects.filter(project__client=self.request.user)
            if self.request.user.user_type=="worker":
                return EOT.objects.filter(project__worker=self.request.user)
        if self.action == 'update_eot':
            if self.request.user.user_type=="builder":
                return EOT.objects.filter(project__builder=self.request.user)
            if self.request.user.user_type=="client":
                return EOT.objects.filter(project__client=self.request.user)
            return EOT.objects.filter(sender=self.request.user)

    def get_serializer_class(self):
        if self.action == 'create'or self.action == 'update_eot':
            return EOTSerializer
        if self.action=='list':
            return EOTListSerializer
        if self.action== 'accept':
            return EOTAcceptSerializer
        if self.action=='retrieve':
            try:
                if EOT.objects.get(pk=self.request.query_params.get('eot_id')).sender.id==self.request.user.id:
                    return EOTDetailsSenderSerializer
                if EOTReceiver.objects.get(eot=self.request.query_params.get('eot_id'),receiver=self.request.user.id).receiver.id==self.request.user.id:
                    return EOTDetailsReceiverSerializer
            except:
               return EOTDetailsNonUserSerializer

    def create(self, request, *args, **kwargs):
        if request.data['receiver']:
            receiver=request.data['receiver']
            request.data["created_by"]=request.user.id
            try:
                    request.data['extend_date_from'] = datetime.datetime.fromtimestamp(
                        int(request.data.get('extend_date_from')))
                    request.data['extend_date_to'] = datetime.datetime.fromtimestamp(
                        int(request.data.get('extend_date_to')))
            except:
                    request.data['extend_date_from'] = datetime.datetime.fromtimestamp(
                        int(request.data.get('extend_date_from'))/1000)
                    request.data['extend_date_to'] = datetime.datetime.fromtimestamp(
                        int(request.data.get('extend_date_to'))/1000)
            request.data['extend_date_from'] = request.data['extend_date_from'].date()
            request.data['extend_date_to'] = request.data['extend_date_to'].date()
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
        else:
            return Response(data='Invalid/Incomplete data', status=status.HTTP_400_BAD_REQUEST)
        for i in receiver:    
            eot= EOT.objects.get(pk=serializer.data.get('id')) 
            receiver = i
            eot.receiver.add(receiver)
            eot.save()
        instance = self.get_queryset().get(pk=serializer.data.get('id'))
        serializer = EOTSerializer(instance)
        headers = self.get_success_headers(serializer.data)
        receivers=request.data['receiver']
        for i in receivers:
            try:
                notification_data={'title':'New Extension Of Time Added',
                'sender_id':serializer.data.get('sender'),
                'receiver_id':i,
                'project':serializer.data.get('project'),
                'eot':serializer.data.get('id'),
                'notification_type':"new_extension_of_time_created",
                'message':"A new extension of time has been created for %s project by %s %s"%(Project.objects.get(pk=serializer.data.get('project')).name,EOT.objects.get(pk=serializer.data.get('id')).sender.first_name,EOT.objects.get(pk=serializer.data.get('id')).sender.last_name)}  
                notification=FCMSerializer(data=notification_data)
                notification.is_valid(raise_exception=True)
                notification.save()
                data_object= {
                        "title": "New Extension Of Time Added",
                        "message": "A new extension of time has been created for %s project by %s %s"%(Project.objects.get(pk=serializer.data.get('project')).name,EOT.objects.get(pk=serializer.data.get('id')).sender.first_name,EOT.objects.get(pk=serializer.data.get('id')).sender.last_name),
                        "notification_type":"new_extension_of_time_created",
                        "project_id":serializer.data.get('project'),
                        "receiver_id":i,
                        "sender_id":request.user.id,
                        "eot_id":serializer.data.get('id'),
                        "fromNotification":True
                }
                send_notification_thread(User.objects.get(pk=notification_data.get("receiver_id")),data_object.get("title"),data_object.get("message"),data_object,len(FcmNotifications.objects.filter(receiver_id=notification_data.get("receiver_id"),watch="false")),request)
            except Exception as e:
                print(e)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
    def retrieve(self, request, *args, **kwargs):
        if request.query_params.get('eot_id'):
            try:
                instance = self.get_queryset().get(
                    pk=request.query_params['eot_id'])
            except:
                instance=EOT.objects.get(
                    pk=request.query_params['eot_id'])
        else:
            return Response('Please specify a EOT ID.', status=status.HTTP_404_NOT_FOUND)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(methods=['delete'], detail=True, url_path="")
    def delete(self, request, *args, **kwargs):
        if request.query_params.get('eot_id'):
            project=EOT.objects.get(id=request.query_params.get('eot_id')).project
            if self.request.user==EOT.objects.get(pk=request.query_params.get('eot_id')).sender or self.request.user==Project.objects.get(id=project.id).builder:
                sender=EOT.objects.get(pk=request.query_params.get('eot_id')).sender
                receivers=EOTReceiver.objects.filter(eot=EOT.objects.get(id=request.query_params.get('eot_id')))
                receivers=[x.receiver for x in receivers]
                for i in receivers:
                    try:
                        notification_data={'title':'Extension Of Time Deleted',
                        'sender_id':request.user.id,
                        'receiver_id':i.id,
                        'notification_type':"extension_of_time_deleted",
                        'message':" Extension Of Time %s has been deleted by %s %s"%(EOT.objects.get(id=request.query_params.get('eot_id')).name,request.user.first_name,request.user.last_name)}  
                        notification=FCMSerializer(data=notification_data)
                        notification.is_valid(raise_exception=True)
                        notification.save()
                        data_object= {
                                "title": "Extension Of Time Deleted",
                                "message":" Extension Of Time %s has been deleted by %s %s"%(EOT.objects.get(id=request.query_params.get('eot_id')).name,request.user.first_name,request.user.last_name),
                                "notification_type":"extension_of_time_deleted",
                                "project_id":project.id,
                                "receiver_id":i.id,
                                "sender_id":request.user.id,
                                "fromNotification":True
                        }
                        send_notification_thread(User.objects.get(pk=notification_data.get("receiver_id")),data_object.get("title"),data_object.get("message"),data_object,len(FcmNotifications.objects.filter(receiver_id=notification_data.get("receiver_id"),watch="false")),request)
                    except Exception as e:
                        print(e)
                obj=EOTReceiver.objects.filter(
                    eot=EOT.objects.get(
                    pk=request.query_params.get('eot_id'))).delete()
                instance = EOT.objects.get(
                    pk=request.query_params.get('eot_id')).delete()
                return Response(data="Extension of Time Deleted Successfully", status=status.HTTP_200_OK)
            else: 
                return Response('You dont have the access to delete this EOT only sender can delete this EOT.', status=status.HTTP_404_NOT_FOUND)
        return Response('Please specify a EOT ID.', status=status.HTTP_404_NOT_FOUND)
        
    @action(methods=['PUT'],detail=False,url_path='update',url_name='update_eot')
    def update_eot(self, request,*args, **kwargs):
        if request.query_params.get('eot_id'):
            try:
                instance = self.get_queryset().get(
                    pk=request.query_params['eot_id'])
            except:
                return Response('Not found.', status=status.HTTP_404_NOT_FOUND)
        else:
            return Response('Please specify a eot_id.', status=status.HTTP_404_NOT_FOUND)
        if request.data['extend_date_from'] or request.data['extend_date_to']:
            try:
                request.data['extend_date_from'] = datetime.datetime.fromtimestamp(
                    int(request.data.get('extend_date_from')))
                request.data['extend_date_to'] = datetime.datetime.fromtimestamp(
                    int(request.data.get('extend_date_to')))
            except:
                request.data['extend_date_from'] = datetime.datetime.fromtimestamp(
                    int(request.data.get('extend_date_from'))/1000)
                request.data['extend_date_to'] = datetime.datetime.fromtimestamp(
                    int(request.data.get('extend_date_to'))/1000)
            request.data['extend_date_from'] = request.data['extend_date_from'].date()
            request.data['extend_date_to'] = request.data['extend_date_to'].date()
            obj_instance=EOT.objects.get(pk=request.query_params['eot_id'])
            serializer = EOTSerializer(instance=obj_instance, data=request.data, partial=True)
            serializer=self.get_serializer(instance,data=request.data,partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.update(instance=instance,validated_data=(request.data))
            headers = self.get_success_headers(serializer.data)
            sender=EOT.objects.get(pk=request.query_params.get('eot_id')).sender
            receivers=EOTReceiver.objects.filter(eot=EOT.objects.get(pk=request.query_params.get('eot_id')))
            for i in receivers:
                i.receiver_watch="false"
                i.save()
            receivers=[x.receiver for x in receivers]
            for i in receivers:
                try:
                    notification_data={'title':'Extension Of Time Updated',
                    'sender_id':request.user.id,
                    'receiver_id':i.id,
                    'project':serializer.data.get('project'),
                    'eot':serializer.data.get('id'),
                    'notification_type':"extension_of_time_updated",
                    'message':"Extension Of Time has been updated for %s project by %s %s"%(Project.objects.get(pk=serializer.data.get('project')).name,request.user.first_name,request.user.last_name)}  
                    notification=FCMSerializer(data=notification_data)
                    notification.is_valid(raise_exception=True)
                    notification.save()
                    data_object= {
                            "title": "Extension Of Time Updated",
                            "message":"Extension Of Time has been updated for %s project by %s %s"%(Project.objects.get(pk=serializer.data.get('project')).name,request.user.first_name,request.user.last_name),
                            "notification_type":"extension_of_time_updated",
                            "project_id":serializer.data.get('project'),
                            "receiver_id":i.id,
                            "sender_id":request.user.id,
                            "eot_id":serializer.data.get('id'),
                            "fromNotification":True
                    }
                    send_notification_thread(User.objects.get(pk=notification_data.get("receiver_id")),data_object.get("title"),data_object.get("message"),data_object,len(FcmNotifications.objects.filter(receiver_id=notification_data.get("receiver_id"),watch="false")),request)
                except Exception as e:
                    print(e)
            return Response(serializer.data,status=status.HTTP_200_OK,headers=headers)
        else:
            obj_instance=EOT.objects.get(pk=request.query_params['eot_id'])
            serializer = EOTSerializer(instance=obj_instance, data=request.data, partial=True)
            serializer=self.get_serializer(instance,data=request.data,partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.update(instance=instance,validated_data=(request.data))
            headers = self.get_success_headers(serializer.data)
            sender=EOT.objects.get(pk=request.query_params.get('eot_id')).sender
            receivers=EOTReceiver.objects.filter(eot=EOT.objects.get(pk=request.query_params.get('eot_id')))
            for i in receivers:
                i.receiver_watch="false"
                i.save()
            receivers=[x.receiver for x in receivers]
            for i in receivers:
                try:
                    notification_data={'title':'Extension Of Time Updated',
                    'sender_id':request.user.id,
                    'receiver_id':i.id,
                    'project':serializer.data.get('project'),
                    'eot':serializer.data.get('id'),
                    'notification_type':"extension_of_time_updated",
                    'message':"Extension Of Time has been updated for %s project by %s %s"%(Project.objects.get(pk=serializer.data.get('project')).name,request.user.first_name,request.user.last_name)}  
                    notification=FCMSerializer(data=notification_data)
                    notification.is_valid(raise_exception=True)
                    notification.save()
                    data_object= {
                            "title": "Extension Of Time Updated",
                            "message":"Extension Of Time has been updated for %s project by %s %s"%(Project.objects.get(pk=serializer.data.get('project')).name,request.user.first_name,request.user.last_name),
                            "notification_type":"extension_of_time_updated",
                            "project_id":serializer.data.get('project'),
                            "receiver_id":i.id,
                            "sender_id":request.user.id,
                            "eot_id":serializer.data.get('id'),
                            "fromNotification":True
                    }
                    send_notification_thread(User.objects.get(pk=notification_data.get("receiver_id")),data_object.get("title"),data_object.get("message"),data_object,len(FcmNotifications.objects.filter(receiver_id=notification_data.get("receiver_id"),watch="false")),request)
                except Exception as e:
                    print(e)
            return Response(serializer.data,status=status.HTTP_200_OK,headers=headers)

    @action(methods=['PUT'],detail=False,url_path='accept',url_name='accept_roi')
    def accept(self, request, *args, **kwargs):
        q = request.query_params
        if not q.get('eot_id') :
            return Response(data='Invalid/Incomplete data', status=status.HTTP_400_BAD_REQUEST)
        instance=EOTReceiver.objects.get(eot=q.get('eot_id'),receiver=request.user)
        serializer = EOTSerializer(instance=instance, data=request.data)
        serializer=self.get_serializer(instance,data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.update(instance=instance,validated_data=(request.data))
        headers = self.get_success_headers(serializer.data)
        obj = EOTReceiver.objects.get(eot=q.get('eot_id'),receiver=request.user)
        obj.action = 'accepted'
        obj.save()
        obj2=EOT.objects.get(pk=q.get('eot_id'))
        obj2.sender_watch = 'false'
        obj2.save()
        try:
            notification_data={'title':'Extension Of Time Signature Submitted',
            'sender_id':self.request.user.id,
            'receiver_id':EOT.objects.get(pk=q.get('eot_id')).sender.id,
            'notification_type':"extension_of_time_signature_submitted",
            'project':EOT.objects.get(pk=q.get('eot_id')).project.id,
            'eot':EOT.objects.get(pk=q.get('eot_id')).id,
            'message':"Extension Of Time Signature has been Submitted by %s %s for %s project"%(request.user.first_name,request.user.last_name,EOT.objects.get(pk=q.get('eot_id')).project.name)}  
            notification=FCMSerializer(data=notification_data)
            notification.is_valid(raise_exception=True)
            notification.save()
            data_object= {
                    "title": "Extension Of Time Signature Submitted",
                    "message":"Extension Of Time Signature has been has been Submitted by %s %s for %s project."%(request.user.first_name,request.user.last_name,EOT.objects.get(pk=q.get('eot_id')).project.name), 
                    "notification_type":"extension_of_time_signature_submitted",
                    "project_id":EOT.objects.get(pk=q.get('eot_id')).project.id,
                    "receiver_id":EOT.objects.get(pk=q.get('eot_id')).sender.id,
                    "eot_id":EOT.objects.get(pk=q.get('eot_id')).id,
                    "sender_id":request.user.id,
                    "fromNotification":True
            }
            send_notification_thread(User.objects.get(pk=notification_data.get("receiver_id")),data_object.get("title"),data_object.get("message"),data_object,len(FcmNotifications.objects.filter(receiver_id=notification_data.get("receiver_id"),watch="false")),request)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        except Exception as e:
            print(e)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def list(self, request, *args, **kwargs):
        if self.filter_queryset(self.get_queryset())==None:
            queryset =EOT.objects.filter(project=request.query_params['project_id']).order_by('-created_date')
        else:
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

class ROIViewset(viewsets.GenericViewSet, mixins.CreateModelMixin, mixins.ListModelMixin,mixins.RetrieveModelMixin):
    def get_permissions(self):
        if self.action == 'update_roi'or self.action == "create" or self.action=='list'or self.action=='retrieve':
            return [IsAuthenticated()]
        return [AllowAny()]

    def get_queryset(self):
        if self.action=='retrieve':
            try:
                if not ROI.objects.get(project__builder=self.request.user) and ROI.objects.get(project__client=self.request.user) and ROI.objects.get(project__worker=self.request.user):
                    return User.objects.filter(pk=self.request.user.id)
            except:
                if self.request.user.user_type=="builder":
                    return ROI.objects.filter(project__builder=self.request.user)
                if self.request.user.user_type=="client":
                    return ROI.objects.filter(project__client=self.request.user)
                if self.request.user.user_type=="worker":
                    return ROI.objects.filter(project__worker=self.request.user)
        if self.action=="submit" or self.action=="create" or self.action=='list':
            if self.request.user.user_type=="builder":
                return ROI.objects.filter(project__builder=self.request.user)
            if self.request.user.user_type=="client":
                return ROI.objects.filter(project__client=self.request.user)
            if self.request.user.user_type=="worker":
                return ROI.objects.filter(project__worker=self.request.user)
        if self.action == 'update_roi':
            if self.request.user.user_type=="builder":
                return ROI.objects.filter(project__builder=self.request.user)
            return ROI.objects.filter(sender=self.request.user)

    def get_serializer_class(self):
        if self.action == 'create' or self.action == 'update_roi':
            return ROISerializer
        if self.action=='list':
            return ROIListSerializer
        if self.action== 'submit':
            return ROISubmissionSerializer
        if self.action=='retrieve':
            try:
                if ROI.objects.get(pk=self.request.query_params.get('roi_id')).sender.id==self.request.user.id:
                    return ROIDetailsSenderSerializer
                if ROIReceiver.objects.get(roi=self.request.query_params.get('roi_id'),receiver=self.request.user.id).receiver.id==self.request.user.id:
                    return ROIDetailsReceiverSerializer
            except:
               return ROIDetailsNonUserSerializer

    def create(self, request, *args, **kwargs):
        if request.data['receiver']:
            receiver=request.data['receiver']
            request.data["created_by"]=request.user.id
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
        else:
            return Response(data='Invalid/Incomplete data', status=status.HTTP_400_BAD_REQUEST)
        for i in receiver:    
            roi= ROI.objects.get(pk=serializer.data.get('id')) 
            receiver = i
            roi.receiver.add(receiver)
            roi.save()
        instance = self.get_queryset().get(pk=serializer.data.get('id'))
        serializer = ROISerializer(instance)
        headers = self.get_success_headers(serializer.data)
        receivers=request.data['receiver']
        for i in receivers:
            try:
                notification_data={'title':'New Request Of Information Added',
                'sender_id':serializer.data.get('sender'),
                'receiver_id':i,
                'project':serializer.data.get('project'),
                'roi':serializer.data.get('id'),
                'notification_type':"new_request_information_created",
                'message':"A new request of information has been created for %s project by %s %s"%(Project.objects.get(pk=serializer.data.get('project')).name,ROI.objects.get(pk=serializer.data.get('id')).sender.first_name,ROI.objects.get(pk=serializer.data.get('id')).sender.last_name)}  
                notification=FCMSerializer(data=notification_data)
                notification.is_valid(raise_exception=True)
                notification.save()
                data_object= {
                        "title": "New Request Of Information Added",
                        "message": "A new request of information has been created for %s project by %s %s"%(Project.objects.get(pk=serializer.data.get('project')).name,ROI.objects.get(pk=serializer.data.get('id')).sender.first_name,ROI.objects.get(pk=serializer.data.get('id')).sender.last_name),
                        "notification_type":"new_request_information_created",
                        "project_id":serializer.data.get('project'),
                        "receiver_id":i,
                        "sender_id":request.user.id,
                        "roi_id":serializer.data.get('id'),
                        "fromNotification":True
                }
                send_notification_thread(User.objects.get(pk=notification_data.get("receiver_id")),data_object.get("title"),data_object.get("message"),data_object,len(FcmNotifications.objects.filter(receiver_id=notification_data.get("receiver_id"),watch="false")),request)
            except Exception as e:
                print(e)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
    def retrieve(self, request, *args, **kwargs):
        if request.query_params.get('roi_id'):
            try:
                instance = self.get_queryset().get(
                    pk=request.query_params['roi_id'])
            except:
                instance=ROI.objects.get(
                    pk=request.query_params['roi_id'])
        else:
            return Response('Please specify a ROI ID.', status=status.HTTP_404_NOT_FOUND)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(methods=['delete'], detail=True, url_path="")
    def delete(self, request, *args, **kwargs):
        if request.query_params.get('roi_id'):
            project=ROI.objects.get(id=request.query_params.get('roi_id')).project
            if self.request.user==ROI.objects.get(pk=request.query_params.get('roi_id')).sender or self.request.user==Project.objects.get(id=project.id).builder:
                sender=ROI.objects.get(id=request.query_params.get('roi_id')).sender
                receivers=ROIReceiver.objects.filter(roi=ROI.objects.get(pk=request.query_params.get('roi_id')))
                receivers=[x.receiver for x in receivers]
                for i in receivers:
                    try:
                        notification_data={'title':'Request Of Information Deleted',
                        'sender_id':request.user.id,
                        'receiver_id':i.id,
                        'notification_type':"request_information_deleted",
                        'message':" Request Of Information %s has been deleted by %s %s"%(ROI.objects.get(pk=request.query_params.get('roi_id')).name,request.user.first_name,request.user.last_name)}  
                        notification=FCMSerializer(data=notification_data)
                        notification.is_valid(raise_exception=True)
                        notification.save()
                        data_object= {
                                "title": "Request Of Information Deleted",
                                "message":" Request Of Information %s has been deleted by %s %s"%(ROI.objects.get(pk=request.query_params.get('roi_id')).name,request.user.first_name,request.user.last_name),
                                "notification_type":"request_information_deleted",
                                "project_id":project.id,
                                "receiver_id":i.id,
                                "sender_id":request.user.id,
                                "fromNotification":True
                        }
                        send_notification_thread(User.objects.get(pk=notification_data.get("receiver_id")),data_object.get("title"),data_object.get("message"),data_object,len(FcmNotifications.objects.filter(receiver_id=notification_data.get("receiver_id"),watch="false")),request)
                    except Exception as e:
                        print(e)
                obj=ROIReceiver.objects.filter(
                    roi=ROI.objects.get(
                    pk=request.query_params.get('roi_id'))).delete()
                instance = ROI.objects.get(
                    pk=request.query_params.get('roi_id')).delete()
                return Response(data="ROI  Deleted Successfully", status=status.HTTP_200_OK)
            else: 
                return Response('You dont have the access to delete this ROI only sender can delete this ROI.', status=status.HTTP_404_NOT_FOUND)
        return Response('Please specify a ROI ID.', status=status.HTTP_404_NOT_FOUND)

    @action(methods=['PUT'],detail=False,url_path='update',url_name='update_roi')
    def update_roi(self, request,*args, **kwargs):
        if request.query_params.get('roi_id'):
            try:
                instance = self.get_queryset().get(
                    pk=request.query_params['roi_id'])
            except:
                return Response('Not found.', status=status.HTTP_404_NOT_FOUND)
        else:
            return Response('Please specify a roi_id.', status=status.HTTP_404_NOT_FOUND)
        obj_instance=ROI.objects.get(pk=request.query_params['roi_id'])
        serializer = ROISerializer(instance=obj_instance, data=request.data, partial=True)
        serializer=self.get_serializer(instance,data=request.data,partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.update(instance=instance,validated_data=(request.data))
        headers = self.get_success_headers(serializer.data)
        sender=ROI.objects.get(pk=request.query_params['roi_id']).sender
        receivers=ROIReceiver.objects.filter(roi=ROI.objects.get(pk=request.query_params['roi_id']))
        for i in receivers:
            i.receiver_watch="false"
            i.save()
        receivers=[x.receiver for x in receivers]
        for i in receivers:
            try:
                notification_data={'title':'Request Of Information Updated',
                'sender_id':request.user.id,
                'receiver_id':i.id,
                'project':serializer.data.get('project'),
                'roi':serializer.data.get('id'),
                'notification_type':"request_information_updated",
                'message':"Request Of Information has been updated for %s project by %s %s"%(Project.objects.get(pk=serializer.data.get('project')).name,request.user.first_name,request.user.last_name)}  
                notification=FCMSerializer(data=notification_data)
                notification.is_valid(raise_exception=True)
                notification.save()
                data_object= {
                        "title": "Request Of Information Updated",
                        "message":"Request Of Information has been updated for %s project by %s %s"%(Project.objects.get(pk=serializer.data.get('project')).name,request.user.first_name,request.user.last_name),
                        "notification_type":"request_information_updated",
                        "project_id":serializer.data.get('project'),
                        "receiver_id":i.id,
                        "sender_id":request.user.id,
                        "roi_id":serializer.data.get('id'),
                        "fromNotification":True
                }
                send_notification_thread(User.objects.get(pk=notification_data.get("receiver_id")),data_object.get("title"),data_object.get("message"),data_object,len(FcmNotifications.objects.filter(receiver_id=notification_data.get("receiver_id"),watch="false")),request)
            except Exception as e:
                print(e)        
        return Response(serializer.data,status=status.HTTP_200_OK,headers=headers)
    
    @action(methods=['PUT'],detail=False,url_path='submit',url_name='submit_roi')
    def submit(self, request, *args, **kwargs):
        q = request.query_params
        if not q.get('roi_id') :
            return Response(data='Invalid/Incomplete data', status=status.HTTP_400_BAD_REQUEST)
        instance=ROIReceiver.objects.get(roi=q.get('roi_id'),receiver=request.user)
        serializer = ROISerializer(instance=instance, data=request.data)
        serializer=self.get_serializer(instance,data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.update(instance=instance,validated_data=(request.data))
        headers = self.get_success_headers(serializer.data)
        obj = ROIReceiver.objects.get(roi=q.get('roi_id'),receiver=request.user)
        obj.action = 'submitted'
        obj.save()
        obj2=ROI.objects.get(pk=q.get('roi_id'))
        obj2.sender_watch = 'false'
        obj2.save()
        try:
            notification_data={'title':'Request Of Information  Response Submitted',
            'sender_id':self.request.user.id,
            'receiver_id':ROI.objects.get(pk=q.get('roi_id')).sender.id,
            'notification_type':"request_information_accepted",
            'project':ROI.objects.get(pk=q.get('roi_id')).project.id,
            'roi':ROI.objects.get(pk=q.get('roi_id')).id,
            'message':"Request of information Response has been Submitted by %s %s for %s project"%(request.user.first_name,request.user.last_name,ROI.objects.get(pk=q.get('roi_id')).project.name)}  
            notification=FCMSerializer(data=notification_data)
            notification.is_valid(raise_exception=True)
            notification.save()
            data_object= {
                    "title": "Request Of Information  Response Submitted",
                    "message":"Request of information Response has been Submitted by %s %s for %s project."%(request.user.first_name,request.user.last_name,ROI.objects.get(pk=q.get('roi_id')).project.name), 
                    "notification_type":"request_information_accepted",
                    "project_id":ROI.objects.get(pk=q.get('roi_id')).project.id,
                    "receiver_id":ROI.objects.get(pk=q.get('roi_id')).sender.id,
                    "roi_id":ROI.objects.get(pk=q.get('roi_id')).id,
                    "sender_id":request.user.id,
                    "fromNotification":True
            }
            send_notification_thread(User.objects.get(pk=notification_data.get("receiver_id")),data_object.get("title"),data_object.get("message"),data_object,len(FcmNotifications.objects.filter(receiver_id=notification_data.get("receiver_id"),watch="false")),request)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        except Exception as e:
            print(e)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def list(self, request, *args, **kwargs):
        if self.filter_queryset(self.get_queryset())==None:
            queryset =ROI.objects.filter(project=request.query_params['project_id']).order_by('-created_date')
        else:
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

class ToolBoxViewset(viewsets.GenericViewSet, mixins.CreateModelMixin, mixins.ListModelMixin,mixins.RetrieveModelMixin):
    def get_permissions(self):
        if self.action == 'update_toolbox' or self.action == "create" or self.action=='list'or self.action=='retrieve':
            return [IsAuthenticated()]
        return [AllowAny()]

    def get_queryset(self):
        if self.action=='retrieve':
            try:
                if not ToolBox.objects.get(project__builder=self.request.user) and ToolBox.objects.get(project__client=self.request.user) and ToolBox.objects.get(project__worker=self.request.user):
                    return User.objects.filter(pk=self.request.user.id)
            except:
                if self.request.user.user_type=="builder":
                    return ToolBox.objects.filter(project__builder=self.request.user)
                if self.request.user.user_type=="client":
                    return ToolBox.objects.filter(project__client=self.request.user)
                if self.request.user.user_type=="worker":
                    return ToolBox.objects.filter(project__worker=self.request.user)
        if self.action=="accept" or self.action=="decline" or self.action=="create"or self.action=='list':
            if self.request.user.user_type=="builder":
                return ToolBox.objects.filter(project__builder=self.request.user)
            if self.request.user.user_type=="client":
                return ToolBox.objects.filter(project__client=self.request.user)
            if self.request.user.user_type=="worker":
                return ToolBox.objects.filter(project__worker=self.request.user)
        if self.action == 'update_toolbox':
            if self.request.user.user_type=="builder":
                return ToolBox.objects.filter(project__builder=self.request.user)
            return ToolBox.objects.filter(sender=self.request.user)

    def get_serializer_class(self):
        if self.action == 'create' or self.action == 'update_toolbox':
            return ToolBoxSerializer
        if self.action=='list':
            return ToolBoxListSerializer
        if self.action=='retrieve':
            try:
                if ToolBox.objects.get(pk=self.request.query_params.get('toolbox_id')).sender.id==self.request.user.id:
                    return ToolBoxDetailsSenderSerializer
                if ToolBoxReceiver.objects.get(toolbox=self.request.query_params.get('toolbox_id'),receiver=self.request.user.id).receiver.id==self.request.user.id:
                    return ToolBoxDetailsReceiverSerializer
            except:
               return ToolBoxDetailsNonUserSerializer


    def create(self, request, *args, **kwargs):
        if request.data['receiver']:
            request.data["created_by"]=request.user.id
            receiver=request.data['receiver']
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
        else:
            return Response(data='Invalid/Incomplete data', status=status.HTTP_400_BAD_REQUEST)
        for i in receiver:    
            toolbox= ToolBox.objects.get(pk=serializer.data.get('id')) 
            receiver = i
            toolbox.receiver.add(receiver)
            toolbox.save()
        instance = self.get_queryset().get(
                    pk=serializer.data.get('id'))
        serializer = ToolBoxSerializer(instance)
        headers = self.get_success_headers(serializer.data)
        receivers=request.data['receiver']
        for i in receivers:
            try:
                notification_data={'title':'New Tool Box Talk Added',
                'sender_id':serializer.data.get('sender'),
                'receiver_id':i,
                'project':serializer.data.get('project'),
                'toolbox':serializer.data.get('id'),
                'notification_type':"new_tool_box_talk_created",
                'message':"A new tool box talk has been created for %s project by %s %s"%(Project.objects.get(pk=serializer.data.get('project')).name,ToolBox.objects.get(pk=serializer.data.get('id')).sender.first_name,ToolBox.objects.get(pk=serializer.data.get('id')).sender.last_name)}  
                notification=FCMSerializer(data=notification_data)
                notification.is_valid(raise_exception=True)
                notification.save()
                data_object= {
                        "title": "New Tool Box Talk Added",
                        "message": "A tool box talk has been created for %s project by %s %s"%(Project.objects.get(pk=serializer.data.get('project')).name,ToolBox.objects.get(pk=serializer.data.get('id')).sender.first_name,ToolBox.objects.get(pk=serializer.data.get('id')).sender.last_name),
                        "notification_type":"new_tool_box_talk_created",
                        "project_id":serializer.data.get('project'),
                        "receiver_id":i,
                        "sender_id":request.user.id,
                        "toolbox_id":serializer.data.get('id'),
                        "fromNotification":True
                }
                send_notification_thread(User.objects.get(pk=notification_data.get("receiver_id")),data_object.get("title"),data_object.get("message"),data_object,len(FcmNotifications.objects.filter(receiver_id=notification_data.get("receiver_id"),watch="false")),request)
            except Exception as e:
                print(e)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def retrieve(self, request, *args, **kwargs):
        if request.query_params.get('toolbox_id'):
            try:
                instance = self.get_queryset().get(
                    pk=request.query_params['toolbox_id'])
            except:
                instance=ToolBox.objects.get(
                    pk=request.query_params['toolbox_id'])
        else:
            return Response('Please specify a toolbox ID.', status=status.HTTP_404_NOT_FOUND)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(methods=['delete'], detail=True, url_path="")
    def delete(self, request, *args, **kwargs):
        if request.query_params.get('toolbox_id'):
            project=ToolBox.objects.get(id=request.query_params.get('toolbox_id')).project
            if self.request.user==ToolBox.objects.get(pk=request.query_params.get('toolbox_id')).sender or self.request.user==Project.objects.get(id=project.id).builder:
                sender=ToolBox.objects.get(pk=request.query_params.get('toolbox_id')).sender
                receivers=ToolBoxReceiver.objects.filter(toolbox=ToolBox.objects.get(pk=request.query_params.get('toolbox_id')))
                receivers=[x.receiver for x in receivers]
                for i in receivers:
                    try:
                        notification_data={'title':'Toolbox Deleted',
                        'sender_id':request.user.id,
                        'receiver_id':i.id,
                        'notification_type':"tool_box_talk_deleted",
                        'message':" Toolbox %s has been deleted by %s %s"%(ToolBox.objects.get(pk=request.query_params.get('toolbox_id')).name,request.user.first_name,request.user.last_name)}  
                        notification=FCMSerializer(data=notification_data)
                        notification.is_valid(raise_exception=True)
                        notification.save()
                        data_object= {
                                "title": "Toolbox Deleted",
                                "message":" Toolbox %s has been deleted by %s %s"%(ToolBox.objects.get(pk=request.query_params.get('toolbox_id')).name,request.user.first_name,request.user.last_name),
                                "notification_type":"tool_box_talk_deleted",
                                "project_id":project.id,
                                "receiver_id":i.id,
                                "sender_id":request.user.id,
                                "fromNotification":True
                        }
                        send_notification_thread(User.objects.get(pk=notification_data.get("receiver_id")),data_object.get("title"),data_object.get("message"),data_object,len(FcmNotifications.objects.filter(receiver_id=notification_data.get("receiver_id"),watch="false")),request)
                    except Exception as e:
                        print(e)
                obj=ToolBoxReceiver.objects.filter(
                    toolbox=ToolBox.objects.get(
                    pk=request.query_params.get('toolbox_id'))).delete()
                instance = ToolBox.objects.get(
                    pk=request.query_params.get('toolbox_id')).delete()
                return Response(data="ToolBox  Deleted Successfully", status=status.HTTP_200_OK)
            else: 
                return Response('You dont have the access to delete this ToolBox only sender can delete this ToolBox.', status=status.HTTP_404_NOT_FOUND)
        return Response('Please specify a ToolBox ID.', status=status.HTTP_404_NOT_FOUND)

    @action(methods=['PUT'],detail=False,url_path='update',url_name='update_toolbox')
    def update_toolbox(self, request,*args, **kwargs):
        if request.query_params.get('toolbox_id'):
            try:
                instance = self.get_queryset().get(
                    pk=request.query_params['toolbox_id'])
            except:
                return Response('Not found.', status=status.HTTP_404_NOT_FOUND)
        else:
            return Response('Please specify a toolbox_id.', status=status.HTTP_404_NOT_FOUND)
        obj_instance=ToolBox.objects.get(pk=request.query_params['toolbox_id'])
        serializer = ToolBoxSerializer(instance=obj_instance, data=request.data, partial=True)
        serializer=self.get_serializer(instance,data=request.data,partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.update(instance=instance,validated_data=(request.data))
        headers = self.get_success_headers(serializer.data)
        sender=ToolBox.objects.get(pk=request.query_params['toolbox_id']).sender
        receivers=ToolBoxReceiver.objects.filter(toolbox=ToolBox.objects.get(pk=request.query_params['toolbox_id']))
        for i in receivers:
                i.receiver_watch="false"
                i.save()
        receivers=[x.receiver for x in receivers]
        for i in receivers:
            try:
                notification_data={'title':'Toolbox Updated',
                'sender_id':request.user.id,
                'receiver_id':i.id,
                'project':serializer.data.get('project'),
                'toolbox':serializer.data.get('id'),
                'notification_type':"tool_box_talk_updated",
                'message':"Toolbox has been updated for %s project by %s %s"%(Project.objects.get(pk=serializer.data.get('project')).name,request.user.first_name,request.user.last_name)}  
                notification=FCMSerializer(data=notification_data)
                notification.is_valid(raise_exception=True)
                notification.save()
                data_object= {
                        "title": "Toolbox Updated",
                        "message":"Toolbox has been updated for %s project by %s %s"%(Project.objects.get(pk=serializer.data.get('project')).name,request.user.first_name,request.user.last_name),
                        "notification_type":"tool_box_talk_updated",
                        "project_id":serializer.data.get('project'),
                        "receiver_id":i.id,
                        "sender_id":request.user.id,
                        "toolbox_id  ":serializer.data.get('id'),
                        "fromNotification":True
                }
                send_notification_thread(User.objects.get(pk=notification_data.get("receiver_id")),data_object.get("title"),data_object.get("message"),data_object,len(FcmNotifications.objects.filter(receiver_id=notification_data.get("receiver_id"),watch="false")),request)
            except Exception as e:
                print(e) 
        return Response(serializer.data,status=status.HTTP_200_OK,headers=headers)
    
    @action(methods=['GET'],detail=False,url_path='accept',url_name='accept_toolbox')
    def accept(self, request, *args, **kwargs):
        q = request.query_params
        if not q.get('toolbox_id') :
            return Response(data='Invalid/Incomplete data', status=status.HTTP_400_BAD_REQUEST)
        obj = ToolBoxReceiver.objects.get(toolbox=q.get('toolbox_id'),receiver=request.user)
        obj.action = 'accepted'
        obj.save()
        obj2=ToolBox.objects.get(pk=q.get('toolbox_id'))
        obj2.sender_watch = 'false'
        obj2.save()
        try:
            notification_data={'title':'Tool Box Talk Accepted',
            'sender_id':self.request.user.id,
            'receiver_id':ToolBox.objects.get(pk=q.get('toolbox_id')).sender.id,
            'notification_type':"tool_box_talk_accepted",
            'project':ToolBox.objects.get(pk=q.get('toolbox_id')).project.id,
            'toolbox':ToolBox.objects.get(pk=q.get('toolbox_id')).id,
            'message':"Tool Box Talk has been accepted by %s %s for %s project"%(request.user.first_name,request.user.last_name,ToolBox.objects.get(pk=q.get('toolbox_id')).project.name)}  
            notification=FCMSerializer(data=notification_data)
            notification.is_valid(raise_exception=True)
            notification.save()
            data_object= {
                    "title": "Tool Box Talk Accepted",
                    "message":"Tool Box Talk has been accepted by %s %s for %s project."%(request.user.first_name,request.user.last_name,ToolBox.objects.get(pk=q.get('toolbox_id')).project.name), 
                    "notification_type":"tool_box_talk_accepted",
                    "project_id":ToolBox.objects.get(pk=q.get('toolbox_id')).project.id,
                    "receiver_id":ToolBox.objects.get(pk=q.get('toolbox_id')).sender.id,
                    "toolbox_id":ToolBox.objects.get(pk=q.get('toolbox_id')).id,
                    "sender_id":request.user.id,
                    "fromNotification":True
            }
            send_notification_thread(User.objects.get(pk=notification_data.get("receiver_id")),data_object.get("title"),data_object.get("message"),data_object,len(FcmNotifications.objects.filter(receiver_id=notification_data.get("receiver_id"),watch="false")),request)
            return Response(data='ToolBox Accepted.', status=status.HTTP_200_OK)
        except Exception as e:
            print(e)
            return Response(data='ToolBox Accepted.', status=status.HTTP_200_OK)
    
    @action(methods=['GET'],detail=False,url_path='decline',url_name='decline_toolbox')
    def decline(self, request, *args, **kwargs):
        q = request.query_params
        if not q.get('toolbox_id') :
            return Response(data='Invalid/Incomplete data', status=status.HTTP_400_BAD_REQUEST)
        obj = ToolBoxReceiver.objects.get(toolbox=q.get('toolbox_id'),receiver=request.user)
        obj.action = 'declined'
        obj.save()
        obj2=ToolBox.objects.get(pk=q.get('toolbox_id'))
        obj2.sender_watch = 'false'
        obj2.save()
        try:
            notification_data={'title':'Tool Box Talk Declined',
            'sender_id':self.request.user.id,
            'receiver_id':ToolBox.objects.get(pk=q.get('toolbox_id')).sender.id,
            'notification_type':"tool_box_talk_declined",
            'project':ToolBox.objects.get(pk=q.get('toolbox_id')).project.id,
            'toolbox':ToolBox.objects.get(pk=q.get('toolbox_id')).id,
            'message':"Tool Box Talk has been declined by %s %s for %s project"%(request.user.first_name,request.user.last_name,ToolBox.objects.get(pk=q.get('toolbox_id')).project.name)}  
            notification=FCMSerializer(data=notification_data)
            notification.is_valid(raise_exception=True)
            notification.save()
            data_object= {
                    "title": "Tool Box Talk Declined",
                    "message":"Tool Box Talk has been declined by %s %s for %s project."%(request.user.first_name,request.user.last_name,ToolBox.objects.get(pk=q.get('toolbox_id')).project.name), 
                    "notification_type":"tool_box_talk_declined",
                    "project_id":ToolBox.objects.get(pk=q.get('toolbox_id')).project.id,
                    "receiver_id":ToolBox.objects.get(pk=q.get('toolbox_id')).sender.id,
                    "toolbox_id":ToolBox.objects.get(pk=q.get('toolbox_id')).id,
                    "sender_id":request.user.id,
                    "fromNotification":True
            }
            send_notification_thread(User.objects.get(pk=notification_data.get("receiver_id")),data_object.get("title"),data_object.get("message"),data_object,len(FcmNotifications.objects.filter(receiver_id=notification_data.get("receiver_id"),watch="false")),request)
            return Response(data='ToolBox Declined.', status=status.HTTP_200_OK)
        except Exception as e:
            print(e)
            return Response(data='ToolBox Declined.', status=status.HTTP_200_OK)
    
    def list(self, request, *args, **kwargs):
        if self.filter_queryset(self.get_queryset())==None:
            queryset =ToolBox.objects.filter(project=request.query_params['project_id']).order_by('-created_date')
        else:
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

class PunchListViewset(viewsets.GenericViewSet, mixins.CreateModelMixin, mixins.ListModelMixin,mixins.RetrieveModelMixin):
    def get_permissions(self):
        if self.action == 'update_punchlist' or self.action == "create" or self.action=='list'or self.action=='retrieve':
            return [IsAuthenticated()]
        return [AllowAny()]

    def get_queryset(self):
        if self.action=='retrieve':
            try:
                if not PunchList.objects.get(project__builder=self.request.user) and PunchList.objects.get(project__client=self.request.user) and PunchList.objects.get(project__worker=self.request.user):
                    return User.objects.filter(pk=self.request.user.id)
            except:
                if self.request.user.user_type=="builder":
                    return PunchList.objects.filter(project__builder=self.request.user)
                if self.request.user.user_type=="client":
                    return PunchList.objects.filter(project__client=self.request.user)
                if self.request.user.user_type=="worker":
                    return PunchList.objects.filter(project__worker=self.request.user)
        if self.action=="completed" or self.action=="mark_uncompleted" or self.action=="create"or self.action=='list':
            if self.request.user.user_type=="builder":
                return PunchList.objects.filter(project__builder=self.request.user)
            if self.request.user.user_type=="client":
                return PunchList.objects.filter(project__client=self.request.user)
            if self.request.user.user_type=="worker":
                return PunchList.objects.filter(project__worker=self.request.user)
        if self.action == 'update_punchlist':
            if self.request.user.user_type=="builder":
                return PunchList.objects.filter(project__builder=self.request.user)
            return PunchList.objects.filter(sender=self.request.user)

    def get_serializer_class(self):
        if self.action == 'create'or self.action == 'update_punchlist' :
            return PunchlistCreateSerializer
        if self.action=='list':
            return PunchlistListSerializer
        if self.action=='retrieve':
            try:
                if PunchList.objects.get(pk=self.request.query_params.get('punchlist_id')).sender.id==self.request.user.id:
                    return PunchlistDetailsSenderSerializer
                if PunchListReceiver.objects.get(punchlist=self.request.query_params.get('punchlist_id'),receiver=self.request.user.id).receiver.id==self.request.user.id:
                    return PunchlistDetailsReceiverSerializer
            except:
               return PunchlistDetailsNonUserSerializer

    def create(self, request, *args, **kwargs):
        if request.data['receiver'] and request.data['checklist']:
            receiver=request.data['receiver']
            request.data["created_by"]=request.user.id
            checklist=request.data['checklist']
            checklist_id=[]
            for i in checklist:
                check_list = CheckListSerializer(data={'name':i})
                check_list.is_valid(raise_exception=False)
                self.perform_create(check_list)
                checklist_id.append(check_list.data.get('id'))
            request.data['checklist']=checklist_id
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
        else:
            return Response(data='Invalid/Incomplete data', status=status.HTTP_400_BAD_REQUEST)
        for i in receiver:    
            Punchlist= PunchList.objects.get(pk=serializer.data.get('id')) 
            receiver = i
            Punchlist.receiver.add(receiver)
            Punchlist.save()
        for i in checklist_id:    
            Punchlist= PunchList.objects.get(pk=serializer.data.get('id')) 
            checklist_id = i
            Punchlist.checklist.add(checklist_id)
            Punchlist.save()
        instance = self.get_queryset().get(
                    pk=serializer.data.get('id'))
        serializer = PunchlistCreateSerializer(instance)
        headers = self.get_success_headers(serializer.data)
        receivers=request.data['receiver']
        for i in receivers:
            try:
                notification_data={'title':'New Punch Added',
                'sender_id':serializer.data.get('sender'),
                'receiver_id':i,
                'project':serializer.data.get('project'),
                'punchlist':serializer.data.get('id'),
                'notification_type':"new_punch_created",
                'message':"A new punch has been created for %s project by %s %s"%(Project.objects.get(pk=serializer.data.get('project')).name,PunchList.objects.get(pk=serializer.data.get('id')).sender.first_name,PunchList.objects.get(pk=serializer.data.get('id')).sender.last_name)}  
                notification=FCMSerializer(data=notification_data)
                notification.is_valid(raise_exception=True)
                notification.save()
                data_object= {
                        "title": "New Punch Added",
                        "message": "A new punch has been created for %s project by %s %s"%(Project.objects.get(pk=serializer.data.get('project')).name,PunchList.objects.get(pk=serializer.data.get('id')).sender.first_name,PunchList.objects.get(pk=serializer.data.get('id')).sender.last_name),
                        "notification_type":"new_punch_created",
                        "project_id":serializer.data.get('project'),
                        "receiver_id":i,
                        "sender_id":request.user.id,
                        "punchlist_id":serializer.data.get('id'),
                        "fromNotification":True
                }
                send_notification_thread(User.objects.get(pk=notification_data.get("receiver_id")),data_object.get("title"),data_object.get("message"),data_object,len(FcmNotifications.objects.filter(receiver_id=notification_data.get("receiver_id"),watch="false")),request)
            except Exception as e:
                print(e)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def retrieve(self, request, *args, **kwargs):
        if request.query_params.get('punchlist_id'):
            try:
                instance = self.get_queryset().get(
                    pk=request.query_params['punchlist_id'])
            except:
                instance=PunchList.objects.get(
                    pk=request.query_params['punchlist_id'])
        else:
            return Response('Please specify a punchlist ID.', status=status.HTTP_404_NOT_FOUND)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


    @action(methods=['delete'], detail=True, url_path="")
    def delete(self, request, *args, **kwargs):
        if request.query_params.get('punchlist_id'):
            project=PunchList.objects.get(id=request.query_params.get('punchlist_id')).project
            if self.request.user==PunchList.objects.get(pk=request.query_params.get('punchlist_id')).sender or self.request.user==Project.objects.get(id=project.id).builder:
                sender=PunchList.objects.get(id=request.query_params.get('punchlist_id')).sender
                receivers=PunchListReceiver.objects.filter(punchlist=PunchList.objects.get(id=request.query_params.get('punchlist_id')))
                receivers=[x.receiver for x in receivers]
                for i in receivers:
                    try:
                        notification_data={'title':'Punch List Deleted',
                        'sender_id':request.user.id,
                        'receiver_id':i.id,
                        'notification_type':"punch_deleted",
                        'message':" Punch List %s has been deleted by %s %s"%(PunchList.objects.get(id=request.query_params.get('punchlist_id')).name,request.user.first_name,request.user.last_name)}  
                        notification=FCMSerializer(data=notification_data)
                        notification.is_valid(raise_exception=True)
                        notification.save()
                        data_object= {
                                "title": "Punch List Deleted",
                                "message":" Punch List %s has been deleted by %s %s"%(PunchList.objects.get(id=request.query_params.get('punchlist_id')).name,request.user.first_name,request.user.last_name),
                                "notification_type":"punch_deleted",
                                "project_id":project.id,
                                "receiver_id":i.id,
                                "sender_id":request.user.id,
                                "fromNotification":True
                        }
                        send_notification_thread(User.objects.get(pk=notification_data.get("receiver_id")),data_object.get("title"),data_object.get("message"),data_object,len(FcmNotifications.objects.filter(receiver_id=notification_data.get("receiver_id"),watch="false")),request)

                    except Exception as e:
                        print(e)
                obj=PunchListReceiver.objects.filter(
                    punchlist=PunchList.objects.get(
                    pk=request.query_params.get('punchlist_id'))).delete()
                obj2=CheckList.objects.filter(
                    punchlist=PunchList.objects.get(
                        pk=request.query_params.get('punchlist_id'))).delete()
                instance = PunchList.objects.get(
                    pk=request.query_params.get('punchlist_id')).delete()
                return Response(data="PunchList  Deleted Successfully", status=status.HTTP_200_OK)
            else: 
                return Response('You dont have the access to delete this PunchList only sender can delete this PunchList.', status=status.HTTP_404_NOT_FOUND)
        return Response('Please specify a PunchList ID.', status=status.HTTP_404_NOT_FOUND)

    @action(methods=['PUT'],detail=False,url_path='update',url_name='update_punchlist')
    def update_punchlist(self, request,*args, **kwargs):
        if request.query_params.get('punchlist_id'):
            try:
                instance = self.get_queryset().get(
                    pk=request.query_params['punchlist_id'])
            except:
                return Response('Not found.', status=status.HTTP_404_NOT_FOUND)
        else:
            return Response('Please specify a punchlist_id.', status=status.HTTP_404_NOT_FOUND)
        if  request.data['checklist']:
            checklistdel=CheckList.objects.filter(punchlist=PunchList.objects.get(pk=request.query_params.get('punchlist_id'))).delete()
            checklist=request.data['checklist']
            checklist_id=[]
            for i in checklist:
                check_list = CheckListSerializer(data={'name':i})
                check_list.is_valid(raise_exception=False)
                self.perform_create(check_list)
                checklist_id.append(check_list.data.get('id'))
            request.data['checklist']=checklist_id
            obj_instance=PunchList.objects.get(pk=request.query_params['punchlist_id'])
            serializer = PunchlistCreateSerializer(instance=obj_instance, data=request.data, partial=True)
            serializer=self.get_serializer(instance,data=request.data,partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.update(instance=instance,validated_data=(request.data))
            headers = self.get_success_headers(serializer.data)
            sender=PunchList.objects.get(pk=request.query_params['punchlist_id']).sender
            receivers=PunchListReceiver.objects.filter(punchlist=PunchList.objects.get(pk=request.query_params['punchlist_id']))
            for i in receivers:
                i.receiver_watch="false"
                i.save()
            receivers=[x.receiver for x in receivers]
            for i in receivers:
                try:
                    notification_data={'title':'Punch List Updated',
                    'sender_id':request.user.id,
                    'receiver_id':i.id,
                    'project':serializer.data.get('project'),
                    'punchlist':serializer.data.get('id'),
                    'notification_type':"punch_updated",
                    'message':"Punch has been updated for %s project by %s %s"%(Project.objects.get(pk=serializer.data.get('project')).name,request.user.first_name,request.user.last_name)}  
                    notification=FCMSerializer(data=notification_data)
                    notification.is_valid(raise_exception=True)
                    notification.save()
                    data_object= {
                            "title": "Punch List Updated",
                            "message":"Punch has been updated for %s project by %s %s"%(Project.objects.get(pk=serializer.data.get('project')).name,request.user.first_name,request.user.last_name),
                            "notification_type":"punch_updated",
                            "project_id":serializer.data.get('project'),
                            "receiver_id":i.id,
                            "sender_id":request.user.id,
                            "punchlist_id":serializer.data.get('id'),
                            "fromNotification":True
                    }
                    send_notification_thread(User.objects.get(pk=notification_data.get("receiver_id")),data_object.get("title"),data_object.get("message"),data_object,len(FcmNotifications.objects.filter(receiver_id=notification_data.get("receiver_id"),watch="false")),request)
                except Exception as e:
                    print(e)  
            return Response(serializer.data,status=status.HTTP_200_OK,headers=headers)
        else:
            obj_instance=PunchList.objects.get(pk=request.query_params['punchlist_id'])
            serializer = PunchlistCreateSerializer(instance=obj_instance, data=request.data, partial=True)
            serializer=self.get_serializer(instance,data=request.data,partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.update(instance=instance,validated_data=(request.data))
            headers = self.get_success_headers(serializer.data)
            sender=PunchList.objects.get(pk=request.query_params['punchlist_id']).sender
            receivers=PunchListReceiver.objects.filter(punchlist=PunchList.objects.get(pk=request.query_params['punchlist_id']))
            receivers=[x.receiver for x in receivers]
            for i in receivers:
                try:
                    notification_data={'title':'Punch List Updated',
                    'sender_id':request.user.id,
                    'receiver_id':i.id,
                    'project':serializer.data.get('project'),
                    'punchlist':serializer.data.get('id'),
                    'notification_type':"punch_updated",
                    'message':"Punch has been updated for %s project by %s %s"%(Project.objects.get(pk=serializer.data.get('project')).name,request.user.first_name,request.user.last_name)}  
                    notification=FCMSerializer(data=notification_data)
                    notification.is_valid(raise_exception=True)
                    notification.save()
                    data_object= {
                            "title": "Punch List Updated",
                            "message":"Punch has been updated for %s project by %s %s"%(Project.objects.get(pk=serializer.data.get('project')).name,request.user.first_name,request.user.last_name),
                            "notification_type":"punch_updated",
                            "project_id":serializer.data.get('project'),
                            "receiver_id":i.id,
                            "sender_id":request.user.id,
                            "punchlist_id":serializer.data.get('id'),
                            "fromNotification":True
                    }
                    send_notification_thread(User.objects.get(pk=notification_data.get("receiver_id")),data_object.get("title"),data_object.get("message"),data_object,len(FcmNotifications.objects.filter(receiver_id=notification_data.get("receiver_id"),watch="false")),request)
                except Exception as e:
                    print(e) 
            return Response(serializer.data,status=status.HTTP_200_OK,headers=headers)
    
    @action(methods=['GET'],detail=False,url_path='completed',url_name='mark_completed')
    def mark_completed(self, request, *args, **kwargs):
        q = request.query_params
        if not q.get('checklist_id') :
            return Response(data='Invalid/Incomplete data', status=status.HTTP_400_BAD_REQUEST)
        obj = CheckList.objects.get(id=q.get('checklist_id'))
        obj.completed = 'true'
        obj.save()
        return Response(data='Checklist mark completed.', status=status.HTTP_200_OK)
    
    @action(methods=['GET'],detail=False,url_path='uncompleted',url_name='mark_uncompleted')
    def mark_uncompleted(self, request, *args, **kwargs):
        q = request.query_params
        if not q.get('checklist_id') :
            return Response(data='Invalid/Incomplete data', status=status.HTTP_400_BAD_REQUEST)
        obj = CheckList.objects.get(id=q.get('checklist_id'))
        obj.completed = 'false'
        obj.save()
        return Response(data='Checklist mark Uncompleted.', status=status.HTTP_200_OK)
    
    def list(self, request, *args, **kwargs):
        if self.filter_queryset(self.get_queryset())==None:
            queryset =PunchList.objects.filter(project=request.query_params['project_id']).order_by('-created_date')
        else:
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
