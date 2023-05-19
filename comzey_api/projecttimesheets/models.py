from django.db import models
from accounts.models import User
from api.models import Project

# Create your models here.
# includes ------------->>>>>>Timesheet 
class Timesheet(models.Model):
    project=models.ForeignKey(
        to=Project, on_delete=models.CASCADE)
    worker= models.ForeignKey(
        to=User, on_delete=models.CASCADE)
    date_added = models.DateTimeField(auto_now_add=True)
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(blank=True,auto_now_add=True)
    worked_hours=models.CharField(max_length=100)