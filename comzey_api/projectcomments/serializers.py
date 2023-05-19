from rest_framework import serializers
from django.conf import settings
from projectcomments.models import Comment

# includes ----------->>>CommentAddSerializer, CommentListSerializer
class CommentAddSerializer(serializers.ModelSerializer):
    created_time= serializers.SerializerMethodField()
    class Meta:
        model=Comment
        fields='__all__'
        extra_kwargs = {'created_time':{'read_only':True}}
    def get_created_time(self, instance):
        return instance.created_time.strftime("%Y-%m-%d %H:%M:%S" )
    def create(self, validated_data):
        dailylog=validated_data.get('dailylog')
        return super().create(validated_data)
    def to_representation(self, instance):
        data={
                            "id": instance.id,
                            
                            "comment": instance.comment,

                            "created_time": instance.created_time.strftime("%Y-%m-%d %H:%M:%S" ),

                            "user":{'id':instance.user.id,'first_name':instance.user.first_name,'last_name':instance.user.last_name,'profile_picture':instance.user.profile_picture},
                            
        }
        return data

class CommentListSerializer(serializers.ModelSerializer):
    created_time= serializers.SerializerMethodField()
    user=serializers.SerializerMethodField()
    class Meta:
        model=Comment
        fields=['id','comment','created_time','user']
    def get_created_time(self, instance):
        return instance.created_time.strftime("%Y-%m-%d %H:%M:%S" )
    def get_user(self,instance):
        return {'id':instance.user.id,'first_name':instance.user.first_name,'last_name':instance.user.last_name,'profile_picture':instance.user.profile_picture}   
