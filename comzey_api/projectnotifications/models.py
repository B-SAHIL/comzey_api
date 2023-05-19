from django.db import models
from accounts.models import User
from api.models import Project
from projectdailylogs.models import DailyLog
from projectplans.models import Plan
from projecttasks.models import Task
from projectdocuments.models import Document,Variations, ROI, EOT,ToolBox,PunchList, IncidentReport, SiteRiskAssessment,Safety

# Create your models here.
# includes FCM Notifications 
class FcmNotifications(models.Model):
    choices=[('project_assigned_client','project_assigned_client'),
            ('project_paused','project_paused'),('project_resumed','project_resumed'),
            ('project_completed','project_completed'),('project_archived','project_archived'),
            ('project_deleted','project_deleted'),('project_leave','project_leave'),
            ('project_assigned_worker','project_assigned_worker'),
            ('worker_assigned_project','worker_assigned_project'),
            ('task_assigned_worker','task_assigned_worker'),
            ('daily_log_created','daily_log_created'),
            ('new_plan_created','new_plan_created'),
            ('new_doc_uploaded','new_doc_uploaded'),
            ('task_accepted','task_accepted'),
            ('task_rejected','task_rejected'),
            ('invite_accepted_client','invite_accepted_client'),
            ('invite_accepted_worker','invite_accepted_worker'),
            ('task_mark_completed','task_mark_completed'),
            ('task_verified','task_verified'),
            ('new_variation_created','new_variation_created'),
            ('variation_accepted','variation_accepted'),
            ('variation_rejected','variation_rejected'),
            ('new_request_information_created','new_request_information_created'),
            ('request_information_accepted','request_information_accepted'),
            ('new_punch_created','new_punch_created'),
            ('new_extension_of_time_created','new_extension_of_time_created'),
            ('extension_of_time_signature_submitted','extension_of_time_signature_submitted'),
            ('new_tool_box_talk_created','new_tool_box_talk_created'),
            ('tool_box_talk_accepted','tool_box_talk_accepted'),
            ('variation_deleted','variation_deleted'),
            ('extension_of_time_deleted','extension_of_time_deleted'),
            ('request_information_deleted','request_information_deleted'),
            ('punch_deleted','punch_deleted'),
            ('tool_box_talk_deleted','tool_box_talk_deleted'),
            ('variation_updated','variation_updated'),
            ('request_information_updated','request_information_updated'),
            ('punch_updated','punch_updated'),
            ('extension_of_time_updated','extension_of_time_updated'),
            ('tool_box_talk_updated','tool_box_talk_updated'),
            ('product_information_added','product_information_added'),
            ('product_information_updated','product_information_updated'),
            ('product_information_deleted','product_information_deleted'),
            ('plan_updated','plan_updated'),
            ('plan_deleted','plan_deleted'),
            ('new_safety_work_method_created','new_safety_work_method_created'),
            ('safety_work_method_updated','safety_work_method_updated'),
            ('new_material_safety_created','new_material_safety_created'),
            ('material_safety_updated','material_safety_updated'),
            ('material_safety_deleted','material_safety_deleted'),
            ('new_work_health_created','new_work_health_created'),
            ('work_health_updated','work_health_updated'),
            ('work_health_deleted','work_health_deleted'),
            ('safety_work_method_deleted','safety_work_method_deleted'),
            ('new_incident_report_created','new_incident_report_created'),
            ('incident_report_updated','incident_report_updated'),
            ('incident_report_deleted','incident_report_deleted'),
            ('new_site_risk_created','new_site_risk_created'),
            ('site_risk_response_submitted','site_risk_response_submitted')]
    watch_choices=[('false','false'),('true','true')]
    title=models.CharField(max_length=100)
    sender_id=models.ForeignKey(
        to=User, on_delete=models.CASCADE)
    receiver_id=models.ForeignKey(
        to=User, on_delete=models.CASCADE,related_name="received_notifications")
    message=models.CharField(max_length=500)
    date=models.DateTimeField(auto_now_add=True)
    notification_type=models.CharField(choices=choices,max_length=200)
    project=models.ForeignKey(to=Project, on_delete=models.CASCADE,null=True,blank=True)
    task=models.ForeignKey(to=Task, on_delete=models.CASCADE,null=True,blank=True)
    dailylog=models.ForeignKey(to=DailyLog, on_delete=models.CASCADE,null=True,blank=True)
    plan=models.ForeignKey(to=Plan, on_delete=models.CASCADE,null=True,blank=True)
    product_information=models.ForeignKey(to=Document, on_delete=models.CASCADE,null=True,blank=True)
    variation=models.ForeignKey(to=Variations, on_delete=models.CASCADE,null=True,blank=True)
    roi=models.ForeignKey(to=ROI, on_delete=models.CASCADE,null=True,blank=True)
    eot=models.ForeignKey(to=EOT, on_delete=models.CASCADE,null=True,blank=True)
    toolbox=models.ForeignKey(to=ToolBox, on_delete=models.CASCADE,null=True,blank=True)
    punchlist=models.ForeignKey(to=PunchList, on_delete=models.CASCADE,null=True,blank=True)
    safety=models.ForeignKey(to=Safety, on_delete=models.CASCADE,null=True,blank=True)
    incident_report=models.ForeignKey(to=IncidentReport, on_delete=models.CASCADE,null=True,blank=True)
    site_risk=models.ForeignKey(to=SiteRiskAssessment, on_delete=models.CASCADE,null=True,blank=True)
    watch=models.CharField(max_length=5,default="false",choices=watch_choices)