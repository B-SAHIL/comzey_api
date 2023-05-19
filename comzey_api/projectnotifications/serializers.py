from rest_framework import serializers
from projectnotifications.models import FcmNotifications

# includes FCMSerializer, FCMListSerializer
class FCMSerializer(serializers.ModelSerializer):
    class Meta:
        model = FcmNotifications        
        fields ='__all__'

class FCMListSerializer(serializers.ModelSerializer):
    sender_id =serializers.SerializerMethodField()
    date=serializers.SerializerMethodField()
    class Meta:
        model = FcmNotifications  
        fields = '__all__'
    def get_sender_id(self, instance):
        return {'id':instance.sender_id.id,'first_name':instance.sender_id.first_name,'last_name':instance.sender_id.last_name,'profile_picture':instance.sender_id.profile_picture}
    def get_date(self, instance):
        return instance.end_time.strftime("%Y-%m-%d %H:%M:%S" )
    def to_representation(self, instance):
        data={
                            "id": instance.id,                           
                            "title": instance.title,
                            "message": instance.message,
                            "notification_type":instance.notification_type,
                            "project_id":instance.project.id if instance.project else -1,
                            'receiver_id':instance.receiver_id.id,
                            "task_id":instance.task.id if instance.task else -1,
                            "daily_id":instance.dailylog.id if instance.dailylog else -1,
                            "plan_id":instance.plan.id if instance.plan else -1,          
                            "product_information_id":instance.product_information.id if instance.product_information else -1,
                            "variation_id":instance.variation.id if instance.variation else -1,
                            "roi_id":instance.roi.id if instance.roi else -1,
                            "eot_id":instance.eot.id if instance.eot else -1,                         
                            "toolbox_id":instance.toolbox.id if instance.toolbox else -1,
                            "punchlist_id":instance.punchlist.id if instance.punchlist else -1,
                            "safety":instance.safety.id if instance.safety else -1,
                            "incident_report":instance.safety.id if instance.safety else -1,
                            "site_risk":instance.safety.id if instance.safety else -1,
                            "sender_id": {'id':instance.sender_id.id,'first_name':instance.sender_id.first_name,'last_name':instance.sender_id.last_name,'profile_picture':instance.sender_id.profile_picture},                   
                    }
        return data