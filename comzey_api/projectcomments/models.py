from django.db import models
from accounts.models import User
from projectdailylogs.models import DailyLog
from projectdocuments.models import Variations, ROI, EOT,ToolBox,PunchList, IncidentReport, SiteRiskAssessment

# Create your models here.
# includes ------------->>>>>>Comment 
class Comment(models.Model):
    dailylog = models.ForeignKey(
        to=DailyLog, to_field='id', on_delete=models.CASCADE,related_name='dailylog_comment',null=True,blank=True)
    variation=models.ForeignKey(
        to=Variations,to_field='id',related_name='variations_comment', on_delete=models.CASCADE,null=True,blank=True)
    roi = models.ForeignKey(
        to=ROI, to_field='id', on_delete=models.CASCADE,related_name='roi_comment',null=True,blank=True)
    eot = models.ForeignKey(
        to=EOT, to_field='id', on_delete=models.CASCADE,related_name='eot_comment',null=True,blank=True)
    toolbox = models.ForeignKey(
        to=ToolBox, to_field='id', on_delete=models.CASCADE,related_name='toolbox_comment',null=True,blank=True)
    punchlist = models.ForeignKey(
        to=PunchList, to_field='id', on_delete=models.CASCADE,related_name='punchlist_comment',null=True,blank=True)
    incident_report = models.ForeignKey(
        to=IncidentReport, to_field='id', on_delete=models.CASCADE,related_name='incident_report_comment',null=True,blank=True)
    site_risk_assessment = models.ForeignKey(
        to=SiteRiskAssessment, to_field='id', on_delete=models.CASCADE,related_name='site_risk_assessment_comment',null=True,blank=True)
    comment=models.TextField()
    created_time=models.DateTimeField(auto_now_add=True)
    user=models.ForeignKey(
        to=User, related_name='comment_user_id', on_delete=models.CASCADE)

