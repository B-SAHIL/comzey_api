from rest_framework import serializers
from projectdocuments.models import EOT, ROI, CheckList, Document, EOTReceiver, Files, IncidentReport, IncidentType, PunchList, ROIReceiver, Safety, SiteRiskAssessment, SiteRiskAssessmentQuestions, ToolBox, ToolBoxReceiver, VariationReceiver, Variations ,SiteRiskAssessmentRelation,SiteRiskAssessmentThrough
from django.conf import settings

# includes---------------->>>>>>>
# DocumentSerializer, DocumentFilesSerializer, SafetySerializer, SiteRiskAssessmentQuestionserializer
# SiteRiskAssessmentSerializer, SiteRiskAssessmentListSerializer, IncidentTypeSerializer,
# IncidentReportSerializer, IncidentReportListSerializer, VariationsSerializer,
# VariationsListSerializer, ROISubmissionSerializer, ROISerializer, ROIListSerializer,
# ROIDetailsReceiverSerializer, ROIDetailsSenderSerializer, ROIDetailsNonUserSerializer,
# VariationsDetailsReceiverSerializer, VariationsDetailsSenderSerializer, VariationsDetailsNonUserSerializer,
# EOTSerializer, EOTAcceptSerializer, EOTListSerializer, EOTDetailsReceiverSerializer,
# EOTDetailsSenderSerializer, EOTDetailsNonUserSerializer, ToolBoxSerializer,
# ToolBoxListSerializer, ToolBoxDetailsReceiverSerializer, ToolBoxDetailsSenderSerializer,
# ToolBoxDetailsNonUserSerializer, CheckListSerializer, PunchlistCreateSerializer,
# PunchlistListSerializer, PunchlistDetailsReceiverSerializer, PunchlistDetailsSenderSerializer,
# PunchlistDetailsNonUserSerializer
class DocumentSerializer(serializers.ModelSerializer):
    files_list=serializers.SerializerMethodField()
    class Meta:
        model=Document
        fields='__all__'
    def get_files_list(self, instance):
        return [{'id':i.id,'file_name':i.file_name,'file_size':i.size}for i in instance.files_list.all()]

class DocumentFilesSerializer(serializers.ModelSerializer):
    class Meta:
        model=Files
        fields='__all__'

class SafetySerializer(serializers.ModelSerializer):
    class Meta:
        model=Safety
        fields='__all__'

class SiteRiskAssessmentQuestionserializer(serializers.ModelSerializer):
    class Meta:
        model=SiteRiskAssessmentQuestions
        fields='__all__'

class SiteRiskAssessmentSerializer(serializers.ModelSerializer):
    class Meta:
        model=SiteRiskAssessment
        fields='__all__'

class SiteRiskAssessmentRelationSerializer(serializers.ModelSerializer):
    class Meta:
        model=SiteRiskAssessmentRelation
        fields='__all__'

class SiteRiskAssessmentThroughSerializer(serializers.ModelSerializer):
    class Meta:
        model=SiteRiskAssessmentThrough
        fields='__all__'

class SiteRiskAssessmentRelationListSerializer(serializers.ModelSerializer):
    created_by=serializers.SerializerMethodField()
    created_date=serializers.SerializerMethodField()
    updated_date=serializers.SerializerMethodField()
    site_risk_assessment_list=serializers.SerializerMethodField()
    class Meta:
        model=SiteRiskAssessmentRelation
        fields='__all__'
    def get_created_by(self,instance):
        return  {'id':instance.created_by.id,'first_name':instance.created_by.first_name,'last_name':instance.created_by.last_name,'email':instance.created_by.email, 'phone':instance.created_by.phone,'profile_picture': instance.created_by.profile_picture}
    def get_site_risk_assessment_list(self,instance):
        return [{'id':i.id,'upload_file': i.upload_file,'assigned_to':{'id':i.assigned_to.id,'first_name':i.assigned_to.first_name,'last_name':i.assigned_to.last_name,'email':i.assigned_to.email, 'phone':i.assigned_to.phone,'profile_picture': i.assigned_to.profile_picture }if i.assigned_to else {},'project':{'id':i.project.id,'name':i.project.name,'created_date':i.project.created_date.strftime("%Y-%m-%d %H:%M:%S" ) ,'status':i.project.status, 'description':i.project.description},'file':i.file,'status_option':i.status_option,'question':{"id":i.question.id,"question":i.question.question},'response':i.response} for i in instance.site_risk_assessment_list.all()]
    def get_created_date(self,instance):
        return instance.created_date.strftime("%Y-%m-%d %H:%M:%S" )
    def get_updated_date(self,instance):
        return instance.updated_date.strftime("%Y-%m-%d %H:%M:%S" ) 
        
class SiteRiskAssessmentListSerializer(serializers.ModelSerializer):
    project=serializers.SerializerMethodField()
    created_by=serializers.SerializerMethodField()
    assigned_to=serializers.SerializerMethodField()
    question=serializers.SerializerMethodField()
    created_date=serializers.SerializerMethodField()
    updated_date=serializers.SerializerMethodField()
    class Meta:
        model=SiteRiskAssessment
        fields='__all__'
    def get_project(self,instance):
        return {'id':instance.project.id,'name':instance.project.name,'created_date':instance.project.created_date.strftime("%Y-%m-%d %H:%M:%S" ) ,'status':instance.project.status, 'description':instance.project.description}
    def get_created_by(self,instance):
        return  {'id':instance.created_by.id,'first_name':instance.created_by.first_name,'last_name':instance.created_by.last_name,'email':instance.created_by.email, 'phone':instance.created_by.phone,'profile_picture': instance.created_by.profile_picture}
    def get_assigned_to(self,instance):
        if instance.assigned_to:
            return {'id':instance.assigned_to.id,'first_name':instance.assigned_to.first_name,'last_name':instance.assigned_to.last_name,'email':instance.assigned_to.email, 'phone':instance.assigned_to.phone,'profile_picture': instance.assigned_to.profile_picture}
        else :
            return {}
    def get_question(self,instance):
        return {"id":instance.question.id,"question":instance.question.question}
    def get_created_date(self,instance):
        return instance.created_date.strftime("%Y-%m-%d %H:%M:%S" )
    def get_updated_date(self,instance):
        return instance.updated_date.strftime("%Y-%m-%d %H:%M:%S" ) 

class IncidentTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = IncidentType
        fields = ['name', 'id']

class IncidentReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = IncidentReport        
        fields ='__all__'

class IncidentReportListSerializer(serializers.ModelSerializer):
    person_completing_form=serializers.SerializerMethodField()
    witness_of_incident=serializers.SerializerMethodField()
    type_of_incident=IncidentTypeSerializer()
    project=serializers.SerializerMethodField()
    created_by=serializers.SerializerMethodField()
    class Meta:
        model = IncidentReport        
        fields ='__all__'
    def get_person_completing_form(self,instance):
        return {'id':instance.person_completing_form.id,'first_name':instance.person_completing_form.first_name,'last_name':instance.person_completing_form.last_name,'phone':instance.person_completing_form.phone,'email':instance.person_completing_form.email,'profile_picture':instance.person_completing_form.profile_picture}
    def get_witness_of_incident(self,instance):
        if instance.witness_of_incident:
            return {'id':instance.witness_of_incident.id,'first_name':instance.witness_of_incident.first_name,'last_name':instance.witness_of_incident.last_name,'phone':instance.witness_of_incident.phone,'email':instance.witness_of_incident.email,'profile_picture':instance.witness_of_incident.profile_picture}
        else:
            return {}
    def get_created_by(self,instance):
        return {'id':instance.created_by.id,'first_name':instance.created_by.first_name,'last_name':instance.created_by.last_name,'phone':instance.created_by.phone,'email':instance.created_by.email,'profile_picture':instance.created_by.profile_picture}
    def get_project(self,instance):
        return{'id':instance.project.id,'name':instance.project.name,'created_date':instance.project.created_date.strftime("%Y-%m-%d %H:%M:%S" ) ,'status':instance.project.status, 'description':instance.project.description},

class VariationsSerializer(serializers.ModelSerializer):
    receiver=serializers.SerializerMethodField()
    created_date=serializers.SerializerMethodField()
    class Meta:
        model=Variations
        fields='__all__'
    def get_receiver(self,instance):
        return [{'id':i.id,'first_name':i.first_name,'last_name':i.last_name,'phone':i.phone,'email':i.email,'profile_picture':i.profile_picture,'occupation':{'id':i.occupation.id,'name':i.occupation.name}} for i in instance.receiver.all()]
    def get_created_date(self, instance):
        return instance.created_date.strftime("%Y-%m-%d %H:%M:%S" )

class VariationsListSerializer(serializers.ModelSerializer):
    receiver=serializers.SerializerMethodField()
    sender=serializers.SerializerMethodField()
    created_date=serializers.SerializerMethodField()
    class Meta:
        model=Variations
        fields='__all__'
    def get_receiver(self,instance):
        return [{'id':i.id,'first_name':i.first_name,'last_name':i.last_name,'phone':i.phone,'email':i.email,'profile_picture':i.profile_picture,'occupation':{'id':i.occupation.id,'name':i.occupation.name}} for i in instance.receiver.all()]
    def get_created_date(self, instance):
        return instance.created_date.strftime("%Y-%m-%d %H:%M:%S" )
    def get_sender(self,instance):
        return {'id':instance.sender.id,
                'first_name':instance.sender.first_name,
                'last_name':instance.sender.last_name,
                'phone':instance.sender.phone,
                'email':instance.sender.email,
                'profile_picture':instance.sender.profile_picture,
                'occupation':{'id':instance.sender.occupation.id,'name':instance.sender.occupation.name}
                    }
           
class ROISubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model=ROIReceiver
        fields=['info_response']
    def to_representation(self, instance):
        data={'id':instance.roi.id,
                'info_response':instance.info_response,
                'action':'submitted'}
        return data

class ROISerializer(serializers.ModelSerializer):
    receiver=serializers.SerializerMethodField()
    created_date=serializers.SerializerMethodField()
    class Meta:
        model=ROI
        fields='__all__'
    def get_receiver(self,instance):
        return [{'id':i.id,'first_name':i.first_name,'last_name':i.last_name,'phone':i.phone,'email':i.email,'profile_picture':i.profile_picture,'occupation':{'id':i.occupation.id,'name':i.occupation.name}} for i in instance.receiver.all()]
    def get_created_date(self, instance):
        return instance.created_date.strftime("%Y-%m-%d %H:%M:%S" )
    
class ROIListSerializer(serializers.ModelSerializer):
    sender=serializers.SerializerMethodField()
    receiver=serializers.SerializerMethodField()
    created_date=serializers.SerializerMethodField()
    class Meta:
        model=ROI
        fields='__all__'
    def get_receiver(self,instance):
        return [{'id':i.id,'first_name':i.first_name,'last_name':i.last_name,'phone':i.phone,'email':i.email,'profile_picture':i.profile_picture,'occupation':{'id':i.occupation.id,'name':i.occupation.name}} for i in instance.receiver.all()]
    def get_created_date(self, instance):
        return instance.created_date.strftime("%Y-%m-%d %H:%M:%S" )
    def get_sender(self,instance):
        return {'id':instance.sender.id,
                'first_name':instance.sender.first_name,
                'last_name':instance.sender.last_name,
                'phone':instance.sender.phone,
                'email':instance.sender.email,
                'profile_picture':instance.sender.profile_picture,
                'occupation':{'id':instance.sender.occupation.id,'name':instance.sender.occupation.name}
                    }

class ROIDetailsReceiverSerializer(serializers.ModelSerializer):
    receiver=serializers.SerializerMethodField()
    sender=serializers.SerializerMethodField()
    created_date=serializers.SerializerMethodField()
    action=serializers.SerializerMethodField()
    info_response=serializers.SerializerMethodField()
    class Meta:
        model=ROI
        fields=['id','action','info_response','name','info_needed','file','created_date','sender','receiver','project']   
    def get_receiver(self,instance):
        return [{'id':i.id,'first_name':i.first_name,'last_name':i.last_name,'phone':i.phone,'email':i.email,'profile_picture':i.profile_picture,'occupation':{'id':i.occupation.id,'name':i.occupation.name},'action':ROIReceiver.objects.get(receiver=i.id,roi_id=self.context['request'].query_params.get('roi_id')).action,'info_response': ROIReceiver.objects.get(receiver=i.id,roi_id=self.context['request'].query_params.get('roi_id')).info_response} for i in instance.receiver.all()]
    def get_created_date(self, instance):
        return instance.created_date.strftime("%Y-%m-%d %H:%M:%S" )  
    def get_action(self,instance):
        action= ROIReceiver.objects.get(receiver=self.context['request'].user,roi_id=self.context['request'].query_params.get('roi_id')).action
        return action
    def get_info_response(self,instance):
        info_response= ROIReceiver.objects.get(receiver=self.context['request'].user,roi_id=self.context['request'].query_params.get('roi_id')).info_response
        return info_response
    def get_sender(self,instance):
        sender={'id':instance.sender.id,
                    'first_name':instance.sender.first_name,
                    'last_name':instance.sender.last_name,
                    'phone':instance.sender.phone,
                    'email':instance.sender.email,
                    'profile_picture':instance.sender.profile_picture,
                    'occupation':{'id':instance.sender.occupation.id,'name':instance.sender.occupation.name},
                    'action':"sender"}

        return sender

class ROIDetailsSenderSerializer(serializers.ModelSerializer):
    receiver=serializers.SerializerMethodField()
    created_date=serializers.SerializerMethodField()
    class Meta:
        model=ROI
        fields='__all__'  
    def get_receiver(self,instance):
        return [{'id':i.id,'first_name':i.first_name,'last_name':i.last_name,'phone':i.phone,'email':i.email,'profile_picture':i.profile_picture,'occupation':{'id':i.occupation.id,'name':i.occupation.name},'action':ROIReceiver.objects.get(receiver=i.id,roi_id=self.context['request'].query_params.get('roi_id')).action,'info_response': ROIReceiver.objects.get(receiver=i.id,roi_id=self.context['request'].query_params.get('roi_id')).info_response} for i in instance.receiver.all()]
    def get_created_date(self, instance):
        return instance.created_date.strftime("%Y-%m-%d %H:%M:%S" ) 
    def to_representation(self, instance):
        data={
            'id':instance.id,
            'action':"sender",
            'name':instance.name,
            'info_needed':instance.info_needed,
            'file':instance.file,
            'created_date':instance.created_date.strftime("%Y-%m-%d %H:%M:%S" ),
            'project':instance.project.id,
            'sender':{'id':instance.sender.id,
                    'first_name':instance.sender.first_name,
                    'last_name':instance.sender.last_name,
                    'phone':instance.sender.phone,
                    'email':instance.sender.email,
                    'profile_picture':instance.sender.profile_picture,
                    'occupation':{'id':instance.sender.occupation.id,'name':instance.sender.occupation.name},
                    'action':"sender"},
            'receiver':[{'id':i.id,'first_name':i.first_name,'last_name':i.last_name,'phone':i.phone,'email':i.email,'profile_picture':i.profile_picture,'occupation':{'id':i.occupation.id,'name':i.occupation.name},'action':ROIReceiver.objects.get(receiver=i.id,roi_id=self.context['request'].query_params.get('roi_id')).action,'info_response': ROIReceiver.objects.get(receiver=i.id,roi_id=self.context['request'].query_params.get('roi_id')).info_response} for i in instance.receiver.all()]
            }
        return data

class ROIDetailsNonUserSerializer(serializers.ModelSerializer):
    receiver=serializers.SerializerMethodField()
    created_date=serializers.SerializerMethodField()
    class Meta:
        model=ROI
        fields='__all__'  
    def get_receiver(self,instance):
        return [{'id':i.id,'first_name':i.first_name,'last_name':i.last_name,'phone':i.phone,'email':i.email,'profile_picture':i.profile_picture,'occupation':{'id':i.occupation.id,'name':i.occupation.name},'action':ROIReceiver.objects.get(receiver=i.id,roi_id=self.context['request'].query_params.get('roi_id')).action,'info_response': ROIReceiver.objects.get(receiver=i.id,roi_id=self.context['request'].query_params.get('roi_id')).info_response} for i in instance.receiver.all()]
    def get_created_date(self, instance):
        return instance.created_date.strftime("%Y-%m-%d %H:%M:%S" ) 
    def to_representation(self, instance):
        data={
            'id':instance.id,
            'action':"non_user",
            'name':instance.name,
            'info_needed':instance.info_needed,
            'file':instance.file,
            'created_date':instance.created_date.strftime("%Y-%m-%d %H:%M:%S" ),
            'project':instance.project.id,
            'sender':{'id':instance.sender.id,
                    'first_name':instance.sender.first_name,
                    'last_name':instance.sender.last_name,
                    'phone':instance.sender.phone,
                    'email':instance.sender.email,
                    'profile_picture':instance.sender.profile_picture,
                    'occupation':{'id':instance.sender.occupation.id,'name':instance.sender.occupation.name},
                    'action':"sender"},
            'receiver': [{'id':i.id,'first_name':i.first_name,'last_name':i.last_name,'phone':i.phone,'email':i.email,'profile_picture':i.profile_picture,'occupation':{'id':i.occupation.id,'name':i.occupation.name},'action':ROIReceiver.objects.get(receiver=i.id,roi_id=self.context['request'].query_params.get('roi_id')).action,'info_response': ROIReceiver.objects.get(receiver=i.id,roi_id=self.context['request'].query_params.get('roi_id')).info_response} for i in instance.receiver.all()]
            }
        return data

class VariationsDetailsReceiverSerializer(serializers.ModelSerializer):
    receiver=serializers.SerializerMethodField()
    sender=serializers.SerializerMethodField()
    created_date=serializers.SerializerMethodField()
    action=serializers.SerializerMethodField()
    class Meta:
        model=Variations
        fields=['id','action','name','summary','gst','file','price','total_price','created_date','sender','receiver','project']   
    def get_receiver(self,instance):
        return [{'id':i.id,'first_name':i.first_name,'last_name':i.last_name,'phone':i.phone,'email':i.email,'profile_picture':i.profile_picture,'occupation':{'id':i.occupation.id,'name':i.occupation.name},'action':VariationReceiver.objects.get(receiver=i.id,variation_id=self.context['request'].query_params.get('variation_id')).action} for i in instance.receiver.all()]
    def get_created_date(self, instance):
        return instance.created_date.strftime("%Y-%m-%d %H:%M:%S" )  
    def get_action(self,instance):
        action= VariationReceiver.objects.get(receiver=self.context['request'].user,variation_id=self.context['request'].query_params.get('variation_id')).action
        return action
    def get_sender(self,instance):
        sender={'id':instance.sender.id,
                    'first_name':instance.sender.first_name,
                    'last_name':instance.sender.last_name,
                    'phone':instance.sender.phone,
                    'email':instance.sender.email,
                    'profile_picture':instance.sender.profile_picture,
                    'occupation':{'id':instance.sender.occupation.id,'name':instance.sender.occupation.name},
                    'action':"sender"}

        return sender

class VariationsDetailsSenderSerializer(serializers.ModelSerializer):
    receiver=serializers.SerializerMethodField()
    created_date=serializers.SerializerMethodField()
    class Meta:
        model=Variations
        fields='__all__'  
    def get_receiver(self,instance):
        return [{'id':i.id,'first_name':i.first_name,'last_name':i.last_name,'phone':i.phone,'email':i.email,'profile_picture':i.profile_picture,'occupation':{'id':i.occupation.id,'name':i.occupation.name},'action':VariationReceiver.objects.get(receiver=i.id,variation_id=self.context['request'].query_params.get('variation_id')).action} for i in instance.receiver.all()]
    def get_created_date(self, instance):
        return instance.created_date.strftime("%Y-%m-%d %H:%M:%S" ) 
    def to_representation(self, instance):
        data={
            'id':instance.id,
            'action':"sender",
            'name':instance.name,
            'summary':instance.summary,
            'gst':instance.gst,
            'file':instance.file,
            'price':instance.price,
            'total_price':instance.total_price,
            'created_date':instance.created_date.strftime("%Y-%m-%d %H:%M:%S" ),
            'project':instance.project.id,
            'sender':{'id':instance.sender.id,
                    'first_name':instance.sender.first_name,
                    'last_name':instance.sender.last_name,
                    'phone':instance.sender.phone,
                    'email':instance.sender.email,
                    'profile_picture':instance.sender.profile_picture,
                    'occupation':{'id':instance.sender.occupation.id,'name':instance.sender.occupation.name},
                    'action':"sender"},
            'receiver':[{'id':i.id,'first_name':i.first_name,'last_name':i.last_name,'phone':i.phone,'email':i.email,'profile_picture':i.profile_picture,'occupation':{'id':i.occupation.id,'name':i.occupation.name},'action':VariationReceiver.objects.get(receiver=i.id,variation_id=self.context['request'].query_params.get('variation_id')).action} for i in instance.receiver.all()]
            }
        return data

class VariationsDetailsNonUserSerializer(serializers.ModelSerializer):
    receiver=serializers.SerializerMethodField()
    created_date=serializers.SerializerMethodField()
    class Meta:
        model=Variations
        fields='__all__'  
    def get_receiver(self,instance):
        return [{'id':i.id,'first_name':i.first_name,'last_name':i.last_name,'phone':i.phone,'email':i.email,'profile_picture':i.profile_picture,'occupation':{'id':i.occupation.id,'name':i.occupation.name},'action':VariationReceiver.objects.get(receiver=i.id,variation_id=self.context['request'].query_params.get('variation_id')).action} for i in instance.receiver.all()]
    def get_created_date(self, instance):
        return instance.created_date.strftime("%Y-%m-%d %H:%M:%S" ) 
    def to_representation(self, instance):
        data={
            'id':instance.id,
            'action':"non_user",
            'name':instance.name,
            'summary':instance.summary,
            'gst':instance.gst,
            'file':instance.file,
            'price':instance.price,
            'total_price':instance.total_price,
            'created_date':instance.created_date.strftime("%Y-%m-%d %H:%M:%S" ),
            'project':instance.project.id,
            'sender':{'id':instance.sender.id,
                    'first_name':instance.sender.first_name,
                    'last_name':instance.sender.last_name,
                    'phone':instance.sender.phone,
                    'email':instance.sender.email,
                    'profile_picture':instance.sender.profile_picture,
                    'occupation':{'id':instance.sender.occupation.id,'name':instance.sender.occupation.name},
                    'action':"sender"},
            'receiver':[{'id':i.id,'first_name':i.first_name,'last_name':i.last_name,'phone':i.phone,'email':i.email,'profile_picture':i.profile_picture,'occupation':{'id':i.occupation.id,'name':i.occupation.name},'action':VariationReceiver.objects.get(receiver=i.id,variation_id=self.context['request'].query_params.get('variation_id')).action} for i in instance.receiver.all()]
            }
        return data

class EOTSerializer(serializers.ModelSerializer):
    receiver=serializers.SerializerMethodField()
    created_date=serializers.SerializerMethodField()
    class Meta:
        model=EOT
        fields=['id','name','number_of_days','reason_for_delay','extend_date_from','extend_date_to','created_date','sender','receiver','project','created_by']
    def get_receiver(self,instance):
        return [{'id':i.id,'first_name':i.first_name,'last_name':i.last_name,'phone':i.phone,'email':i.email,'profile_picture':i.profile_picture,'occupation':{'id':i.occupation.id,'name':i.occupation.name}} for i in instance.receiver.all()]
    def get_created_date(self, instance):
        return instance.created_date.strftime("%Y-%m-%d %H:%M:%S")

class EOTAcceptSerializer(serializers.ModelSerializer):
    class Meta:
        model=EOTReceiver
        fields=['signature']
    def to_representation(self, instance):
        data={'id':instance.eot.id,
                'signature':instance.signature,
                'action':'accepted'}
        return data
    
class EOTListSerializer(serializers.ModelSerializer):
    sender=serializers.SerializerMethodField()
    receiver=serializers.SerializerMethodField()
    created_date=serializers.SerializerMethodField()
    extend_date_from=serializers.SerializerMethodField()
    extend_date_to=serializers.SerializerMethodField()
    class Meta:
        model=EOT
        fields='__all__'
    def get_receiver(self,instance):
        return [{'id':i.id,'first_name':i.first_name,'last_name':i.last_name,'phone':i.phone,'email':i.email,'profile_picture':i.profile_picture,'occupation':{'id':i.occupation.id,'name':i.occupation.name}} for i in instance.receiver.all()]
    def get_created_date(self, instance):
        return instance.created_date.strftime("%Y-%m-%d %H:%M:%S" )
    def get_extend_date_from(self, instance):
        return instance.extend_date_from.strftime("%Y-%m-%d %H:%M:%S" )
    def get_extend_date_to(self, instance):
        return instance.extend_date_to.strftime("%Y-%m-%d %H:%M:%S" )
    def get_sender(self,instance):
        return {'id':instance.sender.id,
                'first_name':instance.sender.first_name,
                'last_name':instance.sender.last_name,
                'phone':instance.sender.phone,
                'email':instance.sender.email,
                'profile_picture':instance.sender.profile_picture,
                'occupation':{'id':instance.sender.occupation.id,'name':instance.sender.occupation.name}
                    }

class EOTDetailsReceiverSerializer(serializers.ModelSerializer):
    receiver=serializers.SerializerMethodField()
    sender=serializers.SerializerMethodField()
    created_date=serializers.SerializerMethodField()
    extend_date_from=serializers.SerializerMethodField()
    extend_date_to=serializers.SerializerMethodField()
    action=serializers.SerializerMethodField()
    signature=serializers.SerializerMethodField()
    class Meta:
        model=EOT
        fields=['id','action','signature','name','number_of_days','reason_for_delay','extend_date_from','extend_date_to','created_date','sender','receiver','project']   
    def get_receiver(self,instance):
        return [{'id':i.id,'first_name':i.first_name,'last_name':i.last_name,'phone':i.phone,'email':i.email,'profile_picture':i.profile_picture,'occupation':{'id':i.occupation.id,'name':i.occupation.name},'action':EOTReceiver.objects.get(receiver=i.id,eot=self.context['request'].query_params.get('eot_id')).action,'signature': EOTReceiver.objects.get(receiver=i.id,eot=self.context['request'].query_params.get('eot_id')).signature} for i in instance.receiver.all()]
    def get_created_date(self, instance):
        return instance.created_date.strftime("%Y-%m-%d %H:%M:%S" )  
    def get_extend_date_from(self, instance):
        return instance.extend_date_from.strftime("%Y-%m-%d %H:%M:%S" )
    def get_extend_date_to(self, instance):
        return instance.extend_date_to.strftime("%Y-%m-%d %H:%M:%S" )
    def get_action(self,instance):
        action= EOTReceiver.objects.get(receiver=self.context['request'].user,eot=self.context['request'].query_params.get('eot_id')).action
        return action
    def get_signature(self,instance):
        signature= EOTReceiver.objects.get(receiver=self.context['request'].user,eot=self.context['request'].query_params.get('eot_id')).signature
        return signature
    def get_sender(self,instance):
        sender={'id':instance.sender.id,
                    'first_name':instance.sender.first_name,
                    'last_name':instance.sender.last_name,
                    'phone':instance.sender.phone,
                    'email':instance.sender.email,
                    'profile_picture':instance.sender.profile_picture,
                    'occupation':{'id':instance.sender.occupation.id,'name':instance.sender.occupation.name},
                    'action':"sender"}

        return sender

class EOTDetailsSenderSerializer(serializers.ModelSerializer):
    receiver=serializers.SerializerMethodField()
    created_date=serializers.SerializerMethodField()
    extend_date_from=serializers.SerializerMethodField()
    extend_date_to=serializers.SerializerMethodField()
    class Meta:
        model=EOT
        fields='__all__'  
    def get_receiver(self,instance):
        return [{'id':i.id,'first_name':i.first_name,'last_name':i.last_name,'phone':i.phone,'email':i.email,'profile_picture':i.profile_picture,'occupation':{'id':i.occupation.id,'name':i.occupation.name},'action':EOTReceiver.objects.get(receiver=i.id,eot=self.context['request'].query_params.get('eot_id')).action,'signature': EOTReceiver.objects.get(receiver=i.id,eot=self.context['request'].query_params.get('eot_id')).signature} for i in instance.receiver.all()]
    def get_created_date(self, instance):
        return instance.created_date.strftime("%Y-%m-%d %H:%M:%S" ) 
    def get_extend_date_from(self, instance):
        return instance.extend_date_from.strftime("%Y-%m-%d %H:%M:%S" )
    def get_extend_date_to(self, instance):
        return instance.extend_date_to.strftime("%Y-%m-%d %H:%M:%S" )
    def to_representation(self, instance):
        data={
            'id':instance.id,
            'action':"sender",
            'name':instance.name,
            'reason_for_delay':instance.reason_for_delay,
            'number_of_days':instance.number_of_days,
            'extend_date_from':instance.extend_date_from.strftime("%Y-%m-%d %H:%M:%S" ) ,
            'extend_date_to':instance.extend_date_to.strftime("%Y-%m-%d %H:%M:%S" ) ,
            'created_date':instance.created_date.strftime("%Y-%m-%d %H:%M:%S" ) ,
            'project':instance.project.id,
            'sender':{'id':instance.sender.id,
                    'first_name':instance.sender.first_name,
                    'last_name':instance.sender.last_name,
                    'phone':instance.sender.phone,
                    'email':instance.sender.email,
                    'profile_picture':instance.sender.profile_picture,
                    'occupation':{'id':instance.sender.occupation.id,'name':instance.sender.occupation.name},
                    'action':"sender"},
            'receiver':[{'id':i.id,'first_name':i.first_name,'last_name':i.last_name,'phone':i.phone,'email':i.email,'profile_picture':i.profile_picture,'occupation':{'id':i.occupation.id,'name':i.occupation.name},'action':EOTReceiver.objects.get(receiver=i.id,eot=self.context['request'].query_params.get('eot_id')).action,'signature': EOTReceiver.objects.get(receiver=i.id,eot=self.context['request'].query_params.get('eot_id')).signature} for i in instance.receiver.all()]
            }
        return data

class EOTDetailsNonUserSerializer(serializers.ModelSerializer):
    receiver=serializers.SerializerMethodField()
    created_date=serializers.SerializerMethodField()
    extend_date_from=serializers.SerializerMethodField()
    extend_date_to=serializers.SerializerMethodField()
    class Meta:
        model=EOT
        fields='__all__'  
    def get_receiver(self,instance):
        return [{'first_name':i.first_name,'last_name':i.last_name,'phone':i.phone,'email':i.email,'profile_picture':i.profile_picture,'occupation':{'id':i.occupation.id,'name':i.occupation.name},'action':EOTReceiver.objects.get(receiver=i.id,eot=self.context['request'].query_params.get('eot_id')).action,'signature': EOTReceiver.objects.get(receiver=i.id,eot=self.context['request'].query_params.get('eot_id')).signature} for i in instance.receiver.all()]
    def get_created_date(self, instance):
        return instance.created_date.strftime("%Y-%m-%d %H:%M:%S" ) 
    def get_extend_date_from(self, instance):
        return instance.extend_date_from.strftime("%Y-%m-%d %H:%M:%S" )
    def get_extend_date_to(self, instance):
        return instance.extend_date_to.strftime("%Y-%m-%d %H:%M:%S" )
    def to_representation(self, instance):
        data={
            'id':instance.id,
            'action':"non_user",
            'name':instance.name,
            'reason_for_delay':instance.reason_for_delay,
            'number_of_days':instance.number_of_days,
            'extend_date_from':instance.extend_date_from.strftime("%Y-%m-%d %H:%M:%S" ) ,
            'extend_date_to':instance.extend_date_to.strftime("%Y-%m-%d %H:%M:%S" ) ,
            'created_date':instance.created_date.strftime("%Y-%m-%d %H:%M:%S" ) ,
            'project':instance.project.id,
            'sender':{'id':instance.sender.id,
                    'first_name':instance.sender.first_name,
                    'last_name':instance.sender.last_name,
                    'phone':instance.sender.phone,
                    'email':instance.sender.email,
                    'profile_picture':instance.sender.profile_picture,
                    'occupation':{'id':instance.sender.occupation.id,'name':instance.sender.occupation.name},
                    'action':"sender"},
            'receiver': [{'id':i.id,'first_name':i.first_name,'last_name':i.last_name,'phone':i.phone,'email':i.email,'profile_picture':i.profile_picture,'occupation':{'id':i.occupation.id,'name':i.occupation.name},'action':EOTReceiver.objects.get(receiver=i.id,eot=self.context['request'].query_params.get('eot_id')).action,'signature': EOTReceiver.objects.get(receiver=i.id,eot=self.context['request'].query_params.get('eot_id')).signature} for i in instance.receiver.all()]
            }
        return data

class ToolBoxSerializer(serializers.ModelSerializer):
    receiver=serializers.SerializerMethodField()
    created_date=serializers.SerializerMethodField()
    class Meta:
        model=ToolBox
        fields='__all__'
    def get_receiver(self,instance):
        return [{'id':i.id,'first_name':i.first_name,'last_name':i.last_name,'phone':i.phone,'email':i.email,'profile_picture':i.profile_picture,'occupation':{'id':i.occupation.id,'name':i.occupation.name}} for i in instance.receiver.all()]
    def get_created_date(self, instance):
        return instance.created_date.strftime("%Y-%m-%d %H:%M:%S" )

class ToolBoxListSerializer(serializers.ModelSerializer):
    sender=serializers.SerializerMethodField()
    receiver=serializers.SerializerMethodField()
    created_date=serializers.SerializerMethodField()
    class Meta:
        model=ToolBox
        fields='__all__'
    def get_receiver(self,instance):
        return [{'id':i.id,'first_name':i.first_name,'last_name':i.last_name,'phone':i.phone,'email':i.email,'profile_picture':i.profile_picture,'occupation':{'id':i.occupation.id,'name':i.occupation.name}} for i in instance.receiver.all()]
    def get_created_date(self, instance):
        return instance.created_date.strftime("%Y-%m-%d %H:%M:%S" )
    def get_sender(self,instance):
        return {'id':instance.sender.id,
                'first_name':instance.sender.first_name,
                'last_name':instance.sender.last_name,
                'phone':instance.sender.phone,
                'email':instance.sender.email,
                'profile_picture':instance.sender.profile_picture,
                'occupation':{'id':instance.sender.occupation.id,'name':instance.sender.occupation.name}
                    }

class ToolBoxDetailsReceiverSerializer(serializers.ModelSerializer):
    receiver=serializers.SerializerMethodField()
    sender=serializers.SerializerMethodField()
    created_date=serializers.SerializerMethodField()
    action=serializers.SerializerMethodField()
    class Meta:
        model=ToolBox
        fields=['id','action','name','topic_of_discussion','remedies','file','created_date','sender','receiver','project']   
    def get_receiver(self,instance):
        return [{'id':i.id,'first_name':i.first_name,'last_name':i.last_name,'phone':i.phone,'email':i.email,'profile_picture':i.profile_picture,'occupation':{'id':i.occupation.id,'name':i.occupation.name},'action':ToolBoxReceiver.objects.get(receiver=i.id,toolbox=self.context['request'].query_params.get('toolbox_id')).action} for i in instance.receiver.all()]
    def get_created_date(self, instance):
        return instance.created_date.strftime("%Y-%m-%d %H:%M:%S" )  
    def get_action(self,instance):
        action= ToolBoxReceiver.objects.get(receiver=self.context['request'].user,toolbox=self.context['request'].query_params.get('toolbox_id')).action
        return action
    def get_sender(self,instance):
        sender={'id':instance.sender.id,
                    'first_name':instance.sender.first_name,
                    'last_name':instance.sender.last_name,
                    'phone':instance.sender.phone,
                    'email':instance.sender.email,
                    'profile_picture':instance.sender.profile_picture,
                    'occupation':{'id':instance.sender.occupation.id,'name':instance.sender.occupation.name},
                    'action':"sender"}

        return sender

class ToolBoxDetailsSenderSerializer(serializers.ModelSerializer):
    receiver=serializers.SerializerMethodField()
    created_date=serializers.SerializerMethodField()
    class Meta:
        model=ToolBox
        fields='__all__'  
    def get_receiver(self,instance):
        return [{'id':i.id,'first_name':i.first_name,'last_name':i.last_name,'phone':i.phone,'email':i.email,'profile_picture':i.profile_picture,'occupation':{'id':i.occupation.id,'name':i.occupation.name},'action':ToolBoxReceiver.objects.get(receiver=i.id,toolbox=self.context['request'].query_params.get('toolbox_id')).action} for i in instance.receiver.all()]
    def get_created_date(self, instance):
        return instance.created_date.strftime("%Y-%m-%d %H:%M:%S" ) 
    def to_representation(self, instance):
        data={
            'id':instance.id,
            'action':"sender",
            'name':instance.name,
            'topic_of_discussion':instance.topic_of_discussion,
            'remedies':instance.remedies,
            'file':instance.file,
            'created_date':instance.created_date.strftime("%Y-%m-%d %H:%M:%S" ) ,
            'project':instance.project.id,
            'sender':{'id':instance.sender.id,
                    'first_name':instance.sender.first_name,
                    'last_name':instance.sender.last_name,
                    'phone':instance.sender.phone,
                    'email':instance.sender.email,
                    'profile_picture':instance.sender.profile_picture,
                    'occupation':{'id':instance.sender.occupation.id,'name':instance.sender.occupation.name},
                    'action':"sender"},
            'receiver':[{'id':i.id,'first_name':i.first_name,'last_name':i.last_name,'phone':i.phone,'email':i.email,'profile_picture':i.profile_picture,'occupation':{'id':i.occupation.id,'name':i.occupation.name},'action':ToolBoxReceiver.objects.get(receiver=i.id,toolbox=self.context['request'].query_params.get('toolbox_id')).action} for i in instance.receiver.all()]
            }
        return data

class ToolBoxDetailsNonUserSerializer(serializers.ModelSerializer):
    receiver=serializers.SerializerMethodField()
    created_date=serializers.SerializerMethodField()
    class Meta:
        model=ToolBox
        fields='__all__'  
    def get_receiver(self,instance):
        return [{'id':i.id,'first_name':i.first_name,'last_name':i.last_name,'phone':i.phone,'email':i.email,'profile_picture':i.profile_picture,'occupation':{'id':i.occupation.id,'name':i.occupation.name},'action':ToolBoxReceiver.objects.get(receiver=i.id,toolbox=self.context['request'].query_params.get('toolbox_id')).action} for i in instance.receiver.all()]
    def get_created_date(self, instance):
        return instance.created_date.strftime("%Y-%m-%d %H:%M:%S" ) 
    def to_representation(self, instance):
        data={
            'id':instance.id,
            'action':"non_user",
            'name':instance.name,
            'topic_of_discussion':instance.topic_of_discussion,
            'remedies':instance.remedies,
            'file':instance.file,
            'created_date':instance.created_date.strftime("%Y-%m-%d %H:%M:%S" ) ,
            'project':instance.project.id,
            'sender':{'id':instance.sender.id,
                    'first_name':instance.sender.first_name,
                    'last_name':instance.sender.last_name,
                    'phone':instance.sender.phone,
                    'email':instance.sender.email,
                    'profile_picture':instance.sender.profile_picture,
                    'occupation':{'id':instance.sender.occupation.id,'name':instance.sender.occupation.name},
                    'action':"sender"},
            'receiver': [{'id':i.id,'first_name':i.first_name,'last_name':i.last_name,'phone':i.phone,'email':i.email,'profile_picture':i.profile_picture,'occupation':{'id':i.occupation.id,'name':i.occupation.name},'action':ToolBoxReceiver.objects.get(receiver=i.id,toolbox=self.context['request'].query_params.get('toolbox_id')).action} for i in instance.receiver.all()]
            }
        return data

class CheckListSerializer(serializers.ModelSerializer):
    class Meta:
        model=CheckList
        fields='__all__'

class PunchlistCreateSerializer(serializers.ModelSerializer):
    receiver=serializers.SerializerMethodField()
    created_date=serializers.SerializerMethodField()
    checklist=serializers.SerializerMethodField()
    class Meta:
        model=PunchList
        fields='__all__'
    def get_receiver(self,instance):
        return [{'id':i.id,'first_name':i.first_name,'last_name':i.last_name,'phone':i.phone,'email':i.email,'profile_picture':i.profile_picture,'occupation':{'id':i.occupation.id,'name':i.occupation.name}} for i in instance.receiver.all()]
    def get_created_date(self, instance):
        return instance.created_date.strftime("%Y-%m-%d %H:%M:%S" )
    def get_checklist(self, instance):
        return [{'id':i.id,'name':i.name,'status':i.completed}for i in instance.checklist.all()]

class PunchlistListSerializer(serializers.ModelSerializer):
    sender=serializers.SerializerMethodField()
    receiver=serializers.SerializerMethodField()
    created_date=serializers.SerializerMethodField()
    checklist=serializers.SerializerMethodField()
    class Meta:
        model=PunchList
        fields='__all__'
    def get_receiver(self,instance):
        return [{'id':i.id,'first_name':i.first_name,'last_name':i.last_name,'phone':i.phone,'email':i.email,'profile_picture':i.profile_picture,'occupation':{'id':i.occupation.id,'name':i.occupation.name}} for i in instance.receiver.all()]
    def get_created_date(self, instance):
        return instance.created_date.strftime("%Y-%m-%d %H:%M:%S" )
    def get_checklist(self, instance):
        return [{'id':i.id,'name':i.name,'status':i.completed}for i in instance.checklist.all()]
    def get_sender(self,instance):
        return {'id':instance.sender.id,
                'first_name':instance.sender.first_name,
                'last_name':instance.sender.last_name,
                'phone':instance.sender.phone,
                'email':instance.sender.email,
                'profile_picture':instance.sender.profile_picture,
                'occupation':{'id':instance.sender.occupation.id,'name':instance.sender.occupation.name}
                    }

class PunchlistDetailsReceiverSerializer(serializers.ModelSerializer):
    receiver=serializers.SerializerMethodField()
    sender=serializers.SerializerMethodField()
    created_date=serializers.SerializerMethodField()
    checklist=serializers.SerializerMethodField()
    action=serializers.SerializerMethodField()
    class Meta:
        model=PunchList
        fields=['id','name','checklist','action','description','file','created_date','sender','receiver','project']   
    def get_receiver(self,instance):
        return [{'id':i.id,'first_name':i.first_name,'last_name':i.last_name,'phone':i.phone,'email':i.email,'profile_picture':i.profile_picture,'occupation':{'id':i.occupation.id,'name':i.occupation.name},'action':'receiver','checklist': [{'id':i.id,'name':i.name,'status':i.completed}for i in instance.checklist.all()]} for i in instance.receiver.all()]
    def get_created_date(self, instance):
        return instance.created_date.strftime("%Y-%m-%d %H:%M:%S" )  
    def get_action(self, instance):
        return 'receiver' 
    def get_checklist(self, instance):
        return [{'id':i.id,'name':i.name,'status':i.completed}for i in instance.checklist.all()]
    def get_sender(self,instance):
        sender={'id':instance.sender.id,
                    'first_name':instance.sender.first_name,
                    'last_name':instance.sender.last_name,
                    'phone':instance.sender.phone,
                    'email':instance.sender.email,
                    'profile_picture':instance.sender.profile_picture,
                    'occupation':{'id':instance.sender.occupation.id,'name':instance.sender.occupation.name},
                    'action':'sender'}
        return sender

class PunchlistDetailsSenderSerializer(serializers.ModelSerializer):
    receiver=serializers.SerializerMethodField()
    sender=serializers.SerializerMethodField()
    created_date=serializers.SerializerMethodField()
    checklist=serializers.SerializerMethodField()
    class Meta:
        model=PunchList
        fields=['id','name','checklist','description','file','created_date','sender','receiver','project']   
    def get_receiver(self,instance):
        return [{'id':i.id,'first_name':i.first_name,'last_name':i.last_name,'phone':i.phone,'email':i.email,'profile_picture':i.profile_picture,'occupation':{'id':i.occupation.id,'name':i.occupation.name},'action':'receiver','checklist': [{'id':i.id,'name':i.name,'status':i.completed}for i in instance.checklist.all()]} for i in instance.receiver.all()]
    def get_created_date(self, instance):
        return instance.created_date.strftime("%Y-%m-%d %H:%M:%S" )  
    def get_checklist(self, instance):
        return [{'id':i.id,'name':i.name,'status':i.completed}for i in instance.checklist.all()]
    def to_representation(self, instance):
        data={
            'id':instance.id,
            'action':"sender",
            'name':instance.name,
            'description':instance.description,
            'file':instance.file,
            'created_date':instance.created_date.strftime("%Y-%m-%d %H:%M:%S" ) ,
            'project':instance.project.id,
            'checklist':[{'id':i.id,'name':i.name,'status':i.completed}for i in instance.checklist.all()],
            'sender':{'id':instance.sender.id,
                    'first_name':instance.sender.first_name,
                    'last_name':instance.sender.last_name,
                    'phone':instance.sender.phone,
                    'email':instance.sender.email,
                    'profile_picture':instance.sender.profile_picture,
                    'occupation':{'id':instance.sender.occupation.id,'name':instance.sender.occupation.name},
                    'action':"sender"},
            'receiver': [{'id':i.id,'first_name':i.first_name,'last_name':i.last_name,'phone':i.phone,'email':i.email,'profile_picture':i.profile_picture,'occupation':{'id':i.occupation.id,'name':i.occupation.name},'action':'receiver','checklist': [{'id':i.id,'name':i.name,'status':i.completed}for i in instance.checklist.all()]} for i in instance.receiver.all()]
            }
        return data

class PunchlistDetailsNonUserSerializer(serializers.ModelSerializer):
    receiver=serializers.SerializerMethodField()
    sender=serializers.SerializerMethodField()
    created_date=serializers.SerializerMethodField()
    checklist=serializers.SerializerMethodField()
    class Meta:
        model=PunchList
        fields=['id','name','checklist','description','file','created_date','sender','receiver','project']   
    def get_receiver(self,instance):
        return [{'id':i.id,'first_name':i.first_name,'last_name':i.last_name,'phone':i.phone,'email':i.email,'profile_picture':i.profile_picture,'occupation':{'id':i.occupation.id,'name':i.occupation.name},'action':'receiver','checklist': [{'id':i.id,'name':i.name,'status':i.completed}for i in instance.checklist.all()]} for i in instance.receiver.all()]
    def get_created_date(self, instance):
        return instance.created_date.strftime("%Y-%m-%d %H:%M:%S" )  
    def get_checklist(self, instance):
        return [{'id':i.id,'name':i.name,'status':i.completed}for i in instance.checklist.all()]
    def to_representation(self, instance):
        data={
            'id':instance.id,
            'action':"non_user",
            'name':instance.name,
            'description':instance.description,
            'file':instance.file,
            'created_date':instance.created_date.strftime("%Y-%m-%d %H:%M:%S" ) ,
            'project':instance.project.id,
            'checklist':[{'id':i.id,'name':i.name,'status':i.completed}for i in instance.checklist.all()],
            'sender':{'id':instance.sender.id,
                    'first_name':instance.sender.first_name,
                    'last_name':instance.sender.last_name,
                    'phone':instance.sender.phone,
                    'email':instance.sender.email,
                    'profile_picture':instance.sender.profile_picture,
                    'occupation':{'id':instance.sender.occupation.id,'name':instance.sender.occupation.name},
                    'action':"sender"},
            'receiver': [{'id':i.id,'first_name':i.first_name,'last_name':i.last_name,'phone':i.phone,'email':i.email,'profile_picture':i.profile_picture,'occupation':{'id':i.occupation.id,'name':i.occupation.name},'action':'receiver','checklist': [{'id':i.id,'name':i.name,'status':i.completed}for i in instance.checklist.all()]} for i in instance.receiver.all()]
            }
        return data