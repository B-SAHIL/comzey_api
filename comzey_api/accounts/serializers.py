import datetime
from django.db.models import fields
from rest_framework import serializers
from accounts.models import InductionAnswers, InductionQuestions, Occupation, User, Invite
from rest_framework_jwt.settings import api_settings

jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER

class OccupationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Occupation
        fields = ['name', 'id']

class RegistrationSerializer(serializers.ModelSerializer):
    jwt_token = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id','jwt_token', 'first_name', 'last_name', 'email', 'phone', 'facebook_token','trial_ended',
                  'apple_token', 'google_token', 'user_type', 'occupation', 'company', 'signature', 'username', 'password','profile_picture','safety_card','trade_licence','invite_id','invite_message']
        extra_kwargs = {'password': {'write_only': True},
                        'username': {'read_only': True},
                        'jwt_token': {'read_only': True},
                        'facebook_token': {'write_only': True},
                        'apple_token': {'write_only': True},
                        'google_token': {'write_only': True},
                        'id':{'read_only':True},}

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = super().create(validated_data)
        user.set_password(password)
        user.save()
        return user

    def save_user(self,instance,context, validated_data):
        password = context.get('password')
        user = super().save()
        user.set_password(password)
        user.save()
        return user

    def get_jwt_token(self, obj):
        obj.username = str(obj.username)
        payload = jwt_payload_handler(obj)
        token = jwt_encode_handler(payload)
        return token

class ProfileDetailsUpdateSerializer(serializers.ModelSerializer):
    occupation=OccupationSerializer()
    class Meta:
        model = User
        fields = ['first_name', 'last_name','phone','occupation', 'company','profile_picture']
    def update(self, instance, validated_data):
        if validated_data.get('occupation'):
            occupation=Occupation.objects.get(pk=validated_data.get('occupation'))
            validated_data['occupation'] = occupation
            return super().update(instance, validated_data)

class InviteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invite
        fields = ['first_name', 'last_name', 'email', 'user_type','phone']

    def create(self, validated_data):
        validated_data['invited_by'] = User.objects.get(pk=self.context['invited_by'])
        invite_obj = super().create(validated_data)
        return invite_obj
    def to_representation(self, instance):
        data={"id": instance.id,
                "first_name":instance.first_name,
                "last_name":instance.last_name,
                "email":instance.email,
                "user_type":instance.user_type,
                "phone":instance.phone,
                "invited_by":instance.invited_by.id}
        return data

class InviteWorkerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invite
        fields = ['first_name', 'last_name', 'email','phone', 'user_type','project','induction_url']

    def create(self, validated_data):
        validated_data['invited_by'] = User.objects.get(pk=self.context['invited_by'])
        invite_obj = super().create(validated_data)
        return invite_obj
    def to_representation(self, instance):
        data={"id": instance.id,
                "first_name":instance.first_name,
                "last_name":instance.last_name,
                "email":instance.email,
                "user_type":instance.user_type,
                "invited_by":instance.invited_by.id,
                "project_id":instance.project.id,
                "phone":instance.phone,
                "induction_url":instance.induction_url}
        return data

class SendMailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invite
        invite_id = serializers.CharField(required=True)
        invite_link = serializers.URLField(required=True)
        exclude = ('id','invited_by','first_name', 'last_name', 'email', 'user_type','invite_date',
        'status','accepted_date','invite_id', )

class LoginSerializer(serializers.ModelSerializer):
    jwt_token = serializers.SerializerMethodField()
    occupation=OccupationSerializer()
    class Meta:
        model = User
        fields = ['id','jwt_token', 'first_name', 'last_name', 'email', 'phone', 'user_type', 'facebook_token','is_subscription','trial_ended',
                  'apple_token', 'google_token', 'occupation', 'company', 'signature', 'username', 'password','profile_picture','safety_card','trade_licence']
        extra_kwargs = {'password': {'write_only': True},
                        'facebook_token': {'write_only': True},
                        'apple_token': {'write_only': True},
                        'google_token': {'write_only': True},
                        'first_name': {'read_only': True},
                        'last_name': {'read_only': True},
                        'user_type': {'read_only': True},
                        'occupation': {'read_only': True},
                        'company': {'read_only': True},
                        'signature': {'read_only': True},
                        'profile_picture': {'read_only': True}}

    def get_jwt_token(self, obj):
        payload = jwt_payload_handler(obj)
        token = jwt_encode_handler(payload)
        return token

class LoginUpdateSerializer(serializers.ModelSerializer):
    occupation=OccupationSerializer()
    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'email', 'phone', 'user_type', 'facebook_token','is_subscription','trial_ended',
                  'apple_token', 'google_token', 'occupation', 'company', 'signature', 'username', 'password','profile_picture','trade_licence','safety_card']
        extra_kwargs = {'password': {'write_only': True},
                        'facebook_token': {'write_only': True},
                        'apple_token': {'write_only': True},
                        'google_token': {'write_only': True},
                        'first_name': {'read_only': True},
                        'last_name': {'read_only': True},
                        'user_type': {'read_only': True},
                        'occupation': {'read_only': True},
                        'company': {'read_only': True},
                        'signature': {'read_only': True},
                        'profile_picture': {'read_only': True}}

class ChangePasswordSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        old_password = serializers.CharField(required=True)
        new_password = serializers.CharField(required=True)
        fields=['id','first_name', 'last_name', 'email', 'phone', 'user_type',]

class InviteListSerializer(serializers.ModelSerializer):
    invite_date=serializers.SerializerMethodField() 
    class Meta:
        model = Invite
        fields = ['id','first_name', 'last_name', 'email', 'user_type','project','induction_url','status','invite_date']
    def get_invite_date(self, instance):
        return instance.invite_date.strftime("%Y-%m-%d %H:%M:%S" ) 

class InductionQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model=InductionQuestions
        fields='__all__'

class InductionAnswersSerializer(serializers.ModelSerializer):
    class Meta:
        model=InductionAnswers
        fields='__all__'

class InductionAnswersListSerializer(serializers.ModelSerializer):
    question=serializers.SerializerMethodField()
    class Meta:
        model=InductionAnswers
        fields='__all__'
    def get_question(self,instance):
        return {'id':instance.question.id,'question':instance.question.question}


