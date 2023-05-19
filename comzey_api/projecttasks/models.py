from django.db import models
from django.contrib.postgres.fields import ArrayField
from accounts.models import User,Occupation
from api.models import Project
# Create your models here.
# includes ------------->>>>>>Task 
class Task(models.Model):
    
    watched_choices=[('false','false'),('true','true')]
    status_choices=[('accepted','accepted'),('pending','pending'),('rejected','rejected')]
    complete_status_choices=[('pending','pending'),('completed','completed'),('verified','verified')]
    task_name = models.CharField(max_length=200)
    color=models.CharField(max_length=200,default='')
    start_date = models.DateField()
    end_date = models.DateField()
    description = models.TextField()
    project = models.ForeignKey(
        to=Project, to_field='id', on_delete=models.CASCADE, related_name='project_id')
    occupation = models.ForeignKey(
        to=Occupation, on_delete=models.CASCADE, related_name='occupation_name')
    assigned_worker = models.ForeignKey(
        to=User, on_delete=models.CASCADE)
    worker_action = models.CharField(max_length=8,choices=status_choices,default='pending')
    documents = ArrayField(
        models.URLField(max_length=200, blank=True,default=[],null=True),
        size=100,blank=True,default=list,null=True,
    ) 
    worker_watch=models.CharField(default='false',max_length=5, choices=watched_choices)
    builder_watch=models.CharField(default='true',max_length=5, choices=watched_choices)
    client_watch=models.CharField(default='true',max_length=5, choices=watched_choices)
    worker_watch_schedule=models.CharField(default='false',max_length=5, choices=watched_choices)
    builder_watch_schedule=models.CharField(default='false',max_length=5, choices=watched_choices)
    client_watch_schedule=models.CharField(default='false',max_length=5, choices=watched_choices)
    complete_status=models.CharField(default='pending',max_length=10,choices=complete_status_choices)  