from django.core.validators import URLValidator
from rest_framework import serializers
from api.models import Address,Project, ProjectWorker, Quotation
from accounts.models import Occupation, User
from django.db.models.query_utils import Q
from django.conf import settings
# includes---------->>>>>>AddressSerializer, QuotationSerializer, CreateProjectSerializer, 
# ListProjectSerializer, WorkerListSerializer, ProjectDetailsSerializer, ProjectWorkerSerializer, 
# ClientListSerializer, AllProjectUsersListSerializer
class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ['name', 'longitude','latitude']

class QuotationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Quotation
        fields = ['file']

class CreateProjectSerializer(serializers.ModelSerializer):
    quotations = serializers.ListField(validators=[URLValidator],write_only=True)
    address=AddressSerializer()
    class Meta:
        model = Project
        fields = ['id','name', 'address', 'client',
                  'description', 'scope_of_work', 'quotations','status']
        write_only_fields = ['quotations']
        extra_kwargs = {'id': {'read_only': True}}
    
    def create(self, validated_data):
        request = self.context.get('request')
        instance = None
        quotations = validated_data.pop('quotations')
        address = validated_data.pop('address')
        address = Address.objects.create(**address)
        validated_data['address'] = address
        instance = Project.objects.create(**validated_data,builder=request.user)
        for quotation in quotations:
            temp = {'project':instance,'file':quotation}
            Quotation.objects.create(**temp)
        return instance

class ListProjectSerializer(serializers.ModelSerializer):
    created_date = serializers.SerializerMethodField()
    class Meta:
        model = Project
        fields = ['id','name', 'created_date','status', 'description']

    def get_created_date(self, instance):
        return instance.created_date.strftime("%Y-%m-%d %H:%M:%S" )

class WorkerListSerializer(serializers.ModelSerializer):
    occupation = serializers.SerializerMethodField()
    class Meta:
        model=User
        fields=['id','first_name','last_name','phone','email','profile_picture','occupation','trade_licence','safety_card']
    def get_occupation(self, instance):
        return {'id':instance.occupation.id, 'name':instance.occupation.name}
    
class ProjectDetailsSerializer(serializers.ModelSerializer):
    # quotations = QuotationSerializer(many=True)
    quotations = serializers.SerializerMethodField()
    builder = serializers.SerializerMethodField()
    address=AddressSerializer()  
    client=  serializers.SerializerMethodField()
    worker= serializers.SerializerMethodField()
    created_date = serializers.SerializerMethodField()
    class Meta:
        model = Project
        fields = ['id','name', 'address', 'client', 'description', 'scope_of_work',
                  'created_date', 'last_updated', 'worker', 'status', 'quotations','builder']

    def get_quotations(self, instance):
        return [i.file for i in instance.quotations.all()]
    def get_builder(self, instance):
        return {'id':instance.builder.id,'first_name':instance.builder.first_name,'last_name':instance.builder.last_name,'phone':instance.builder.phone,'email':instance.builder.email,'profile_picture':instance.builder.profile_picture}
    def get_client(self,instance):
        return {'id':instance.client.id,'first_name':instance.client.first_name,'last_name':instance.client.last_name,'phone':instance.client.phone,'email':instance.client.email,'profile_picture':instance.client.profile_picture}
    def get_worker(self,instance):
        return [{'id':i.id,'first_name':i.first_name,'last_name':i.last_name,'phone':i.phone,'email':i.email,'profile_picture':i.profile_picture,'occupation':{'id':i.occupation.id,'name':i.occupation.name}} for i in instance.worker.all()]
    def get_created_date(self, instance):
        return instance.created_date.strftime("%Y-%m-%d %H:%M:%S" )    

class ProjectWorkerSerializer(serializers.ModelSerializer):
    project=serializers.SerializerMethodField()
    class Meta:
        model=ProjectWorker
        fields=['project']
    def get_project(self,instance):
        return [{'id':instance.project.id,'name':instance.project.name,'created_date':instance.project.created_date.strftime("%Y-%m-%d %H:%M:%S" ) ,'status':instance.project.status, 'description':instance.project.description}]

class ClientListSerializer(serializers.ModelSerializer):
    class Meta:
        model=User
        fields=['id','first_name','last_name','email','phone','profile_picture']

class AllProjectUsersListSerializer(serializers.ModelSerializer):
    builder = serializers.SerializerMethodField() 
    client=  serializers.SerializerMethodField()
    worker= serializers.SerializerMethodField()
    class Meta:
        model = Project
        fields = [ 'client','worker','builder']

    def get_builder(self, instance):
        return {'id':instance.builder.id,'first_name':instance.builder.first_name,'last_name':instance.builder.last_name,'phone':instance.builder.phone,'email':instance.builder.email,'profile_picture':instance.builder.profile_picture,'user_type':instance.builder.user_type}
    def get_client(self,instance):
        return {'id':instance.client.id,'first_name':instance.client.first_name,'last_name':instance.client.last_name,'phone':instance.client.phone,'email':instance.client.email,'profile_picture':instance.client.profile_picture,'user_type':instance.client.user_type}
    def get_worker(self,instance):
        return [{'id':i.id,'first_name':i.first_name,'last_name':i.last_name,'phone':i.phone,'email':i.email,'profile_picture':i.profile_picture,'user_type':i.user_type,'occupation':{'id':i.occupation.id,'name':i.occupation.name}} for i in instance.worker.all()]    


