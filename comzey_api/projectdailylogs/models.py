from django.db import models
from django.contrib.postgres.fields import ArrayField
from accounts.models import User
from api.models import Project
# Create your models here.
# includes --------------->>>>>>>>>>Address, Weather, DailyLog
class Address(models.Model):
    name = models.CharField(max_length=50)
    longitude=models.FloatField()
    latitude=models.FloatField()

class Weather(models.Model):
    current=models.CharField(max_length=10)
    maximum=models.CharField(max_length=10)
    weather_type=models.CharField(max_length=30)
    icon=models.URLField()

class DailyLog(models.Model):
    watched_choices=[('false','false'),('true','true')]
    project = models.ForeignKey(
        to=Project, to_field='id', on_delete=models.CASCADE)
    created_by=models.ForeignKey (
        to=User, to_field='id', on_delete=models.CASCADE)
    weather = models.ForeignKey(
        to=Weather, on_delete=models.CASCADE, related_name='weather')
    location=models.ForeignKey(to=Address, on_delete=models.CASCADE)
    created_time=models.DateTimeField(auto_now_add=True)
    updated_time=models.DateTimeField(auto_now=True)
    documents=ArrayField(
        models.URLField(max_length=200, blank=True,default=[],null=True),
        size=100,blank=True,default=list,null=True,
    )
    notes=models.TextField()
    worker_watch=models.CharField(default='false',max_length=5, choices=watched_choices)
    builder_watch=models.CharField(default='false',max_length=5, choices=watched_choices)
    client_watch=models.CharField(default='false',max_length=5, choices=watched_choices)
