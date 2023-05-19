from django.db import models
from accounts.models import User
from api.models import Project
from django.contrib.postgres.fields import ArrayField

# Create your models here.
# includes------------------>> 
# SiteRiskAssessmentQuestions, Files, FilesDocument, Document, Safety
# SiteRiskAssessment, IncidentType, IncidentReport, VariationReceiver, Variations, ROIReceiver, ROI
# EOTReceiver, EOT, ToolBoxReceiver, ToolBox, PunchListReceiver, CheckList, CheckListPunchList, PunchList

class SiteRiskAssessmentQuestions(models.Model):
    question=models.TextField()
    created_date=models.DateTimeField(auto_now_add=True)
    updated_date=models.DateTimeField(auto_now=True)
    created_by=models.ForeignKey(
        to=User, on_delete=models.CASCADE)

class Files(models.Model):
    file_name=models.URLField(max_length=2000, blank=True,default=[],null=True)
    size=models.CharField(max_length=1200)

class FilesDocument(models.Model):
    document = models.ForeignKey(to='projectdocuments.Document', on_delete=models.DO_NOTHING)
    file = models.ForeignKey(to=Files, on_delete=models.CASCADE)

class Document(models.Model):
    watched_choices=[('false','false'),('true','true')]
    choices=[('specifications_and_product_information',
                    'specifications_and_product_information')]
    project = models.ForeignKey(
        to=Project, on_delete=models.CASCADE)
    created_by=models.ForeignKey (
        to=User, to_field='id', on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    description = models.TextField()
    supplier_details=models.TextField()
    files_list = models.ManyToManyField(to=Files, through=FilesDocument)
    # size=models.CharField(max_length=1200)
    # file=ArrayField(
    #     models.URLField(max_length=200, blank=True,default=[],null=True),
    #     size=100,blank=True,default=list,null=True,
    # )
    type=models.CharField(max_length=38, choices=choices) 
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)
    worker_watch=models.CharField(default='false',max_length=5, choices=watched_choices)
    builder_watch=models.CharField(default='false',max_length=5, choices=watched_choices)
    client_watch=models.CharField(default='false',max_length=5, choices=watched_choices)

class Safety(models.Model):
    watched_choices=[('false','false'),('true','true')]
    choices=[('safe_work_method_statement','safe_work_method_statement'),
                    ('material_safety_data_sheets','material_safety_data_sheets'),
                    ('work_health_and_safety_plan','work_health_and_safety_plan')]
    project = models.ForeignKey(
        to=Project, on_delete=models.CASCADE)
    created_by=models.ForeignKey (
        to=User, to_field='id', on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    description = models.TextField()
    file=ArrayField(
        models.URLField(max_length=200, blank=True,default=[],null=True),
        size=100,blank=True,default=list,null=True,
    )
    type=models.CharField(max_length=38, choices=choices)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)
    worker_watch=models.CharField(default='false',max_length=5, choices=watched_choices)
    client_watch=models.CharField(default='false',max_length=5, choices=watched_choices)

class SiteRiskAssessment(models.Model):
    watched_choices=[('false','false'),('true','true')]
    choices=[('yes','yes'),('no','no'),('NA','NA')]   
    status_option=models.CharField(max_length=3,choices=choices,blank=True)
    file=models.URLField(max_length=2000,blank=True)
    created_by=models.ForeignKey (
        to=User, to_field='id', on_delete=models.CASCADE)
    project = models.ForeignKey(
        to=Project, on_delete=models.CASCADE)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)
    question=models.ForeignKey(
        to= SiteRiskAssessmentQuestions, on_delete=models.CASCADE)
    assigned_to=models.ForeignKey (
        to=User, to_field='id', on_delete=models.CASCADE,related_name="assign_to",null=True,blank=True)    
    response=models.CharField(default='',max_length=5, choices=choices)      
    assigned_to_watch=models.CharField(default='false',max_length=5, choices=watched_choices)    
    builder_watch=models.CharField(default='true',max_length=5, choices=watched_choices)    
    upload_file=models.URLField(max_length=200, blank=True,default="",null=True)       

class SiteRiskAssessmentThrough(models.Model):
    siteriskassessmentrelation = models.ForeignKey(to='projectdocuments.SiteRiskAssessmentRelation', on_delete=models.DO_NOTHING)
    siteriskassessment=models.ForeignKey (
        to=SiteRiskAssessment, to_field='id', on_delete=models.CASCADE,related_name="SiteRiskAssessment_id")
    project = models.ForeignKey(
        to=Project, on_delete=models.CASCADE)
class SiteRiskAssessmentRelation(models.Model):
    site_risk_assessment_list=models.ManyToManyField(to=SiteRiskAssessment, through=SiteRiskAssessmentThrough)
    created_by=models.ForeignKey (
        to=User, to_field='id', on_delete=models.CASCADE,related_name="SiteRiskAssessmentRelationCreated_by")
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)                                                                                                                            

class IncidentType(models.Model):
    name = models.CharField(max_length=50)

class IncidentReport(models.Model):
    watched_choices=[('false','false'),('true','true')]
    time_of_incident_reported=models.TimeField()
    date_of_incident_reported=models.DateField()
    date_of_incident=models.DateField()
    time_of_incident=models.TimeField()
    report_created_date = models.DateTimeField(auto_now_add=True)
    report_updated_date = models.DateTimeField(auto_now=True)
    person_completing_form=models.ForeignKey (
        to=User, to_field='id', on_delete=models.CASCADE,related_name='person_completing_form_id')
    description_of_incident=models.TextField()
    witness_of_incident=models.ForeignKey (
        to=User, to_field='id', on_delete=models.CASCADE,related_name='witness_of_incident',null=True,blank=True)
    preventative_action_taken=models.TextField()
    type_of_incident=models.ForeignKey(to=IncidentType, on_delete=models.CASCADE)
    files=ArrayField(
        models.URLField(max_length=200, blank=True,default=[],null=True),
        size=100,blank=True,default=list,null=True,
    ) 
    project = models.ForeignKey(
        to=Project, on_delete=models.CASCADE)
    created_by=models.ForeignKey (
        to=User, to_field='id', on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    person_completing_form_watch=models.CharField(default='false',max_length=5, choices=watched_choices)
    witness_of_incident_watch=models.CharField(default='false',max_length=5, choices=watched_choices)
    visitor_witness=models.CharField(default='',max_length=100,blank=True) 
    visitor_witness_phone=models.CharField(default='',max_length=100,blank=True) 

class VariationReceiver(models.Model):
    watched_choices=[('false','false'),('true','true')]
    status_choices=[('accepted','accepted'),('pending','pending'),('rejected','rejected')]
    variation = models.ForeignKey(to='projectdocuments.Variations', on_delete=models.DO_NOTHING)
    receiver = models.ForeignKey(to=User, on_delete=models.CASCADE)
    action=models.CharField(max_length=8,choices=status_choices,default='pending')
    receiver_watch=models.CharField(default='false',max_length=5, choices=watched_choices)

class Variations(models.Model):
    watched_choices=[('false','false'),('true','true')]
    sender=models.ForeignKey(
        to=User, on_delete=models.CASCADE,related_name="sender")
    receiver=models.ManyToManyField(to=User, through=VariationReceiver)
    project = models.ForeignKey(
        to=Project, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    summary = models.TextField()
    gst = models.BooleanField(default=False, blank=True, null=True)
    file=ArrayField(
        models.URLField(max_length=200, blank=True,default=[],null=True),
        size=100,blank=True,default=list,null=True,
    ) 
    price=models.CharField(max_length=38)
    total_price=models.CharField(max_length=38)
    created_date = models.DateTimeField(auto_now_add=True)
    sender_watch=models.CharField(default='true',max_length=5, choices=watched_choices)
    created_by=models.ForeignKey (
        to=User, to_field='id',related_name='created_by', on_delete=models.CASCADE)

class ROIReceiver(models.Model):
    watched_choices=[('false','false'),('true','true')]
    status_choices=[('submitted','submitted'),('pending','pending')]
    roi = models.ForeignKey(to='projectdocuments.ROI', on_delete=models.DO_NOTHING)
    receiver = models.ForeignKey(to=User, on_delete=models.CASCADE)
    action=models.CharField(max_length=20,choices=status_choices,default='pending')
    info_response=models.TextField()
    receiver_watch=models.CharField(default='false',max_length=5, choices=watched_choices)

class ROI(models.Model):
    watched_choices=[('false','false'),('true','true')]
    sender=models.ForeignKey(
        to=User, on_delete=models.CASCADE,related_name="ROI_sender")
    receiver=models.ManyToManyField(to=User, through=ROIReceiver)
    project = models.ForeignKey(
        to=Project, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    info_needed = models.TextField()
    file=ArrayField(
        models.URLField(max_length=200, blank=True,default=[],null=True),
        size=100,blank=True,default=list,null=True,
    ) 
    created_date = models.DateTimeField(auto_now_add=True)
    sender_watch=models.CharField(default='true',max_length=5, choices=watched_choices)
    created_by=models.ForeignKey (
        to=User, to_field='id',related_name='created_by_roi', on_delete=models.CASCADE)

class EOTReceiver(models.Model):
    watched_choices=[('false','false'),('true','true')]
    status_choices=[('accepted','accepted'),('pending','pending')]
    eot = models.ForeignKey(to='projectdocuments.EOT', on_delete=models.DO_NOTHING)
    receiver = models.ForeignKey(to=User, on_delete=models.CASCADE)
    action=models.CharField(max_length=20,choices=status_choices,default='pending')
    signature=models.URLField(default="")
    receiver_watch=models.CharField(default='false',max_length=5, choices=watched_choices)

class EOT(models.Model):
    watched_choices=[('false','false'),('true','true')]
    sender=models.ForeignKey(
        to=User, on_delete=models.CASCADE,related_name="EOT_sender")
    receiver=models.ManyToManyField(to=User, through=EOTReceiver)
    project = models.ForeignKey(
        to=Project, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    reason_for_delay = models.TextField()
    number_of_days=models.CharField(max_length=20)
    created_date = models.DateTimeField(auto_now_add=True)
    extend_date_from=models.DateField()
    extend_date_to=models.DateField()
    sender_watch=models.CharField(default='true',max_length=5, choices=watched_choices)
    created_by=models.ForeignKey (
        to=User, to_field='id',related_name='created_by_eot', on_delete=models.CASCADE)

class ToolBoxReceiver(models.Model):
    watched_choices=[('false','false'),('true','true')]
    status_choices=[('accepted','accepted'),('pending','pending'),('declined','declined')]
    toolbox = models.ForeignKey(to='projectdocuments.ToolBox', on_delete=models.DO_NOTHING)
    receiver = models.ForeignKey(to=User, on_delete=models.CASCADE)
    action=models.CharField(max_length=20,choices=status_choices,default='pending')
    receiver_watch=models.CharField(default='false',max_length=5, choices=watched_choices)

class ToolBox(models.Model):
    watched_choices=[('false','false'),('true','true')]
    sender=models.ForeignKey(
        to=User, on_delete=models.CASCADE,related_name="TOOLBOX_sender")
    receiver=models.ManyToManyField(to=User, through=ToolBoxReceiver)
    project = models.ForeignKey(
        to=Project, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    topic_of_discussion = models.TextField()
    remedies=models.TextField()
    created_date = models.DateTimeField(auto_now_add=True)
    file=ArrayField(
        models.URLField(max_length=200, blank=True,default=[],null=True),
        size=100,blank=True,default=list,null=True,
    ) 
    sender_watch=models.CharField(default='true',max_length=5, choices=watched_choices)
    created_by=models.ForeignKey (
        to=User, to_field='id',related_name='created_by_toolbox', on_delete=models.CASCADE)

class PunchListReceiver(models.Model):
    watched_choices=[('false','false'),('true','true')]
    punchlist = models.ForeignKey(to='projectdocuments.PunchList', on_delete=models.DO_NOTHING,related_name='punchlist_id')
    receiver = models.ForeignKey(to=User, on_delete=models.CASCADE)
    receiver_watch=models.CharField(default='false',max_length=5, choices=watched_choices)

class CheckList(models.Model):
    status_choices=[('true','true'),('false','false')]
    completed=models.CharField(max_length=20,choices=status_choices,default='false')
    name=models.TextField()

class CheckListPunchList(models.Model):
    punchlist = models.ForeignKey(to='projectdocuments.PunchList', on_delete=models.DO_NOTHING)
    checklist = models.ForeignKey(to=CheckList, on_delete=models.CASCADE)

class PunchList(models.Model):
    watched_choices=[('false','false'),('true','true')]
    sender=models.ForeignKey(
        to=User, on_delete=models.CASCADE,related_name="punchlist_sender")
    receiver=models.ManyToManyField(to=User, through=PunchListReceiver)
    project = models.ForeignKey(
        to=Project, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    description = models.TextField()
    created_date = models.DateTimeField(auto_now_add=True)
    file=ArrayField(
        models.URLField(max_length=200, blank=True,default=[],null=True),
        size=100,blank=True,default=list,null=True,
    ) 
    checklist=models.ManyToManyField(to=CheckList, through=CheckListPunchList)
    sender_watch=models.CharField(default='true',max_length=5, choices=watched_choices)
    created_by=models.ForeignKey (
        to=User, to_field='id',related_name='created_by_punch', on_delete=models.CASCADE)
