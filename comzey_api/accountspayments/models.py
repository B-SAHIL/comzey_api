from django.db import models
from accounts.models import User
# Create your models here.
# includes --------->>>>>>Product, Plans, Subscription, OutstandingBalance, Subscriber, CycleExecutions, 
# BillingInfo, Payment

class Product(models.Model):
    name = models.CharField(max_length=500,unique=True)
    created_date=models.DateTimeField(auto_now_add=True)
    updated_date=models.DateTimeField(auto_now=True)

class Plans(models.Model):
    name = models.CharField(max_length=500,unique=True)
    product=models.ForeignKey(
        to=Product, to_field='name', on_delete=models.CASCADE, related_name='product_id')
    created_date=models.DateTimeField(auto_now_add=True)
    updated_date=models.DateTimeField(auto_now=True)

class Subscription(models.Model):

    name = models.CharField(max_length=500,unique=True,default='')
    status=models.CharField(max_length=500,default='APPROVAL_PENDING')
    plan=models.ForeignKey(
        to=Plans, to_field="name", on_delete=models.CASCADE, related_name='plan_name',default='')
    start_time=models.DateTimeField()
    create_time=models.DateTimeField(auto_now_add=True)

class OutstandingBalance(models.Model):
    currency_code=models.CharField(max_length=50)
    value=models.CharField(max_length=50)

class Subscriber(models.Model):
    email_address=models.EmailField(unique=True, null=True, default='')
    payer_id=models.CharField(max_length=500)

class CycleExecutions(models.Model):
    tenure_type=models.CharField(max_length=500)
    sequence=models.IntegerField()
    cycles_completed=models.IntegerField()
    cycles_remaining=models.IntegerField()
    current_pricing_scheme_version=models.IntegerField()
    total_cycles=models.IntegerField()

class BillingInfo(models.Model):
    outstanding_balance=models.ForeignKey(to=OutstandingBalance, on_delete=models.CASCADE)
    cycle_executions=models.ForeignKey(to=CycleExecutions, on_delete=models.CASCADE)
    next_billing_time=models.DateTimeField()
    failed_payments_count=models.IntegerField()

class Payment(models.Model):
    user=models.ForeignKey(
        to=User, on_delete=models.CASCADE,related_name="payment_user")
    status=models.CharField(max_length=500,default='APPROVAL_PENDING')
    plan=models.ForeignKey(
        to=Plans, to_field='name', on_delete=models.CASCADE, related_name='plan_id',default='')
    subscription=models.ForeignKey(
        to=Subscription, to_field='name', on_delete=models.CASCADE,default='', related_name='Subscription_id')
    start_time=models.DateTimeField()
    create_time=models.DateTimeField()
    status_update_time=models.DateTimeField()
    plan_overridden=models.BooleanField(default=False)
    update_time=models.DateTimeField()
    subscriber=models.ForeignKey(to=Subscriber, on_delete=models.CASCADE,default='')
    billing_info=models.ForeignKey(to=BillingInfo, on_delete=models.CASCADE,default='')