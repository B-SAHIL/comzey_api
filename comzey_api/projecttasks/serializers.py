from rest_framework import serializers
from django.conf import settings
from projecttasks.models import Task

# includes ----------->>>TaskSerializer, TasksListSerializer,ScheduleWorkerSerializer
class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task        
        fields = '__all__'
    def to_representation(self, instance):
        data={
        "id": instance.id,
        "task_name": instance.task_name ,
        "start_date": instance.start_date.strftime("%Y-%m-%d %H:%M:%S" ) ,
        "end_date": instance.end_date.strftime("%Y-%m-%d %H:%M:%S" ),
        "description":instance.description ,
        "documents": 
            instance.documents
        ,
        "project": {'id':instance.project.id,'name':instance.project.name,'created_date':instance.project.created_date.strftime("%Y-%m-%d %H:%M:%S" ) ,'status':instance.project.status, 'description':instance.project.description}
         ,
        "occupation": {'id':instance.occupation.id,'name':instance.occupation.name,},
        "assigned_worker":{'id':instance.assigned_worker.id,'first_name':instance.assigned_worker.first_name,'last_name':instance.assigned_worker.last_name,'email':instance.assigned_worker.email, 'phone':instance.assigned_worker.phone,'profile_picture': instance.assigned_worker.profile_picture},
        "worker_action":instance.worker_action,
        "complete_status":instance.complete_status,
        "color": instance.color
    }
        return data

class TasksListSerializer(serializers.ModelSerializer):
    assigned_worker= serializers.SerializerMethodField()
    start_date= serializers.SerializerMethodField()
    end_date= serializers.SerializerMethodField()
    class Meta:
        model = Task
        fields = ['task_name','description','assigned_worker','id','worker_action','start_date','end_date','complete_status','color']
    def get_assigned_worker(self,instance):
        return {'id':instance.assigned_worker.id,'first_name':instance.assigned_worker.first_name,'last_name':instance.assigned_worker.last_name,'phone':instance.assigned_worker.phone,'email':instance.assigned_worker.email,'profile_picture':instance.assigned_worker.profile_picture,'occupation':{'id':instance.assigned_worker.occupation.id,'name':instance.assigned_worker.occupation.name}}  
    def get_start_date(self, instance):
        return instance.start_date.strftime("%Y-%m-%d %H:%M:%S" )   
    def get_end_date(self, instance):
        return instance.end_date.strftime("%Y-%m-%d %H:%M:%S" )  

class ScheduleWorkerSerializer(serializers.ModelSerializer):

    class Meta:
        model = Task        
        fields = ['id','color','task_name','start_date','end_date','description','documents','project']
    def to_representation(self, instance):
        data={
        "id": instance.id,
        "task_name": instance.task_name ,
        "start_date": instance.start_date.strftime("%Y-%m-%d %H:%M:%S" ) ,
        "end_date": instance.end_date.strftime("%Y-%m-%d %H:%M:%S" ),
        "description":instance.description ,
        "color":instance.color,
        "documents": 
            instance.documents
        ,
        "project": {'id':instance.project.id,'name':instance.project.name,'created_date':instance.project.created_date.strftime("%Y-%m-%d %H:%M:%S" ) ,'status':instance.project.status, 'description':instance.project.description}
    }
        return data
