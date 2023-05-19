from django.db import models
from accounts.models import Occupation, User
from django.contrib.postgres.fields import ArrayField
  
# Create your models here.
# includes Address, ProjectWorker, Project, Quotation
class Address(models.Model):
    name = models.CharField(max_length=50)
    longitude=models.FloatField()
    latitude=models.FloatField()

class ProjectWorker(models.Model):
    watched_choices=[('false','false'),('true','true')]
    project = models.ForeignKey(to='api.Project', on_delete=models.DO_NOTHING)
    worker = models.ForeignKey(to=User, on_delete=models.CASCADE)
    leave = models.BooleanField(default=False, blank=True, null=True)
    timesheet_status=models.CharField(max_length=5,default='false')
    worker_watch=models.CharField(default='false',max_length=5, choices=watched_choices)
    client_watch=models.CharField(default='false',max_length=5, choices=watched_choices)
    builder_watch=models.CharField(default='false',max_length=5, choices=watched_choices)

class Project(models.Model):
    status_choices = [('in_progress', 'in_progress'), ('completed',
                                                       'completed'), ('archived', 'archived'), ('paused', 'paused')]
    name = models.CharField(max_length=200)
    address = models.ForeignKey(to=Address, on_delete=models.CASCADE)
    client = models.ForeignKey(
        to=User, related_name='project_client', on_delete=models.CASCADE)
    builder = models.ForeignKey(to=User,related_name='project_builder', on_delete=models.CASCADE)
    description = models.TextField()
    scope_of_work = ArrayField(
        models.URLField(max_length=200, blank=True,default=[],null=True),
        size=100, blank=True,default=list,null=True,
    ) 
    created_date = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    worker = models.ManyToManyField(to=User, through=ProjectWorker)
    status = models.CharField(max_length=12, choices=status_choices, blank=True,null=True,default='in_progress')

class Quotation(models.Model):
    project = models.ForeignKey(
        to=Project, on_delete=models.CASCADE, related_name='quotations')
    file = models.URLField(blank=True,default=list,null=True,)

    def __str__(self):
        return self.file


