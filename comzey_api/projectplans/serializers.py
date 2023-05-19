from rest_framework import serializers
from django.conf import settings
from projectplans.models import Plan
# includes ----------->>>PlanSerializer
class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model=Plan
        fields='__all__'
