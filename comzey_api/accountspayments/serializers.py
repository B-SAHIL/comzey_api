from rest_framework import serializers
from accountspayments.models import Payment,Plans,Product,Subscription,OutstandingBalance,Subscriber,BillingInfo,CycleExecutions

# includes ----------------------->>>>>>>>>>>>CreateProductSerializer, CreatePlansSerializer, 
# CreateSubscriptionSerializer, CreatePaymentSerializer, OutstandingBalanceSerializer, 
# SubscriberSerializer, CycleExecutionsSerializer, BillingInfoSerializer, GetSubscriptionIdSerializer

class CreateProductSerializer(serializers.ModelSerializer):
    class Meta:
        model=Product
        fields='__all__'

class CreatePlansSerializer(serializers.ModelSerializer):
    class Meta:
        model=Plans
        fields='__all__'

class CreateSubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model=Subscription
        fields='__all__'

class CreatePaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model=Payment
        fields='__all__'

class OutstandingBalanceSerializer(serializers.ModelSerializer):
    class Meta:
        model=OutstandingBalance
        fields='__all__'

class SubscriberSerializer(serializers.ModelSerializer):
    class Meta:
        model=Subscriber
        fields='__all__'

class CycleExecutionsSerializer(serializers.ModelSerializer):
    class Meta:
        model=CycleExecutions
        fields='__all__'

class BillingInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model=BillingInfo
        fields='__all__'

class GetSubscriptionIdSerializer(serializers.ModelSerializer):
    class Meta:
        model=Payment
        fields=['subscription','status']
