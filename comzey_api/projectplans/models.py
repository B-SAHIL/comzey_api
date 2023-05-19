from django.db import models
from accounts.models import User
from django.contrib.postgres.fields import ArrayField
from api.models import Project
# Create your models here.
# includes ------------->>>>>>Plan 
class Plan(models.Model):
    watched_choices=[('false','false'),('true','true')]
    project = models.ForeignKey(
        to=Project, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    description = models.TextField()
    file= ArrayField(
        models.URLField(max_length=200, blank=True,default=[],null=True),
        size=100,blank=True,default=list,null=True,
    ) 
    created_by=models.ForeignKey (
        to=User, to_field='id', on_delete=models.CASCADE)
    created_date = models.DateTimeField(auto_now_add=True)
    worker_watch=models.CharField(default='false',max_length=5, choices=watched_choices)
    builder_watch=models.CharField(default='false',max_length=5, choices=watched_choices)
    client_watch=models.CharField(default='false',max_length=5, choices=watched_choices)
