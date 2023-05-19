from datetime import datetime, timedelta
from time import timezone
from django.db import models
from django.contrib.auth.models import AbstractUser, UserManager
import uuid
from django.forms import BooleanField
from django.utils.translation import gettext_lazy as _
from rest_framework import status
from datetime import date,timedelta
from django.utils.crypto import get_random_string

# Create your models here.
# includes ------->>>>Occupation, User, Invite, InductionQuestions, InductionAnswers
class Occupation(models.Model):
    name = models.CharField(max_length=50,unique=True)

class User(AbstractUser):
    user_type_choices = [('builder', 'builder'), ('worker',
                                              'worker'), ('client', 'client')]
    subscription_choices=[('TRIAL','TRIAL'),('REGULAR','REGULAR'),('NO_ACTIVE_PLAN','NO_ACTIVE_PLAN')]
    invite_id = models.ForeignKey(to='accounts.Invite', on_delete=models.CASCADE,default="",
            related_name="invite_user_id",null=True)
    created_date = models.DateTimeField(auto_now_add=True)
    trial_ended=models.DateField(default=date.today()+timedelta(days=30))
    is_subscription=models.CharField(max_length=20, choices=subscription_choices,default='TRIAL')
    first_name = models.CharField(max_length=20)
    last_name = models.CharField(max_length=20)
    email = models.EmailField(unique=True, null=True, default='')
    phone = models.CharField(max_length=15, null=True, blank=True, default="")
    user_type = models.CharField(max_length=7, choices=user_type_choices)
    facebook_token = models.TextField(null=True, blank=True, default='')
    apple_token = models.TextField(null=True, blank=True, default='')
    google_token = models.TextField(null=True, blank=True, default='')
    occupation = models.ForeignKey(to=Occupation, on_delete=models.CASCADE)
    company = models.CharField(max_length=100)
    signature = models.URLField(blank=True, default='')
    password = models.CharField(_('password'), max_length=128, null=True,blank=True)
    profile_picture=models.URLField(blank=True, default='')
    is_induction=models.BooleanField(default=False)
    safety_card=models.URLField(blank=True, default='')
    trade_licence=models.URLField(blank=True, default='')
    message = models.TextField(null=True, blank=True, default='')
    invite_message = models.TextField(null=True, blank=True, default='')
    username = models.CharField(
        max_length=191, auto_created=True, default=uuid.uuid4, unique=True)
   
    
    
    def save(self, *args, **kwargs):
        if self.is_superuser:
            default_occupation = Occupation.objects.get(id=1)
            self.occupation = default_occupation
            self.user_type = "admin"
        super().save(*args, **kwargs)

    # def generate_password_reset_token(self):
    # # Generate a random string for the password reset token
    #     token = get_random_string(length=32)
    #     # Save the token to the user instance
    #     self.password_reset_token = token
    #     self.save()
    #     return token
    
    class Meta:
        constraints = [
            models.CheckConstraint(
                name="%(app_label)s_%(class)s_email_or_social",
                check=(
                    models.Q(email__isnull=False) |
                    models.Q(facebook_token__isnull=False) |
                    models.Q(apple_token__isnull=False) |
                    models.Q(google_token__isnull=False)
                ),
            ),
            models.UniqueConstraint(fields=[
                                    'email', 'facebook_token', 'apple_token', 'google_token'], name='unique_identity')
        ]




from api.models import Project
class Invite(models.Model):
    user_type_choices = [('worker', 'worker'), ('client', 'client')]
    accepted_choices=[('accepted','accepted'),('pending','pending'),('rejected','rejected')]
    invited_by = models.ForeignKey(
        to=User, on_delete=models.CASCADE,related_name="builder_id")
    first_name = models.CharField(max_length=20)
    last_name = models.CharField(max_length=20)
    email = models.EmailField(unique=True, null=True, default='')
    user_type = models.CharField(max_length=6, choices=user_type_choices)
    invite_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=8,choices=accepted_choices,default='pending')
    accepted_date = models.DateTimeField(null=True, blank=True)
    invite_id =  models.CharField(
        max_length=191, auto_created=True, default=uuid.uuid4, unique=True)
    project=models.ForeignKey(to=Project, on_delete=models.CASCADE,null=True,blank=True)
    induction_url=models.URLField(blank=True)
    phone = models.CharField(max_length=15, null=True, blank=True, default="")

class InductionQuestions(models.Model):
    choices=[('FALSE','FALSE'),('TRUE','TRUE'),('YES','YES'),('BLANK','BLANK'),('NO','NO')]
    question=models.TextField()
    updated_date=models.DateTimeField(auto_now=True)
    created_by=models.ForeignKey(
        to=User, on_delete=models.CASCADE)
    created_date=models.DateTimeField(auto_now_add=True)
    correct_answer=models.CharField(max_length=500,choices=choices,default='')

class InductionAnswers(models.Model):
    choices=[('FALSE','FALSE'),('TRUE','TRUE'),('YES','YES'),('BLANK','BLANK'),('NO','NO')]
    question=models.ForeignKey(
        to=InductionQuestions,on_delete=models.CASCADE,default='')
    answer=models.CharField(max_length=500,choices=choices,default='')
    created_date=models.DateTimeField(auto_now_add=True)
    answered_by=models.ForeignKey(to=User, on_delete=models.CASCADE)

