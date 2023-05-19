from ast import Return
from datetime import datetime, timedelta
from time import timezone
from rest_framework import serializers
from django.conf import settings
from api.models import ProjectWorker
from api.serializers import AddressSerializer
from projecttimesheets.models import Timesheet

# includes ----------->>>TimesheetCreateSerializer, TimesheetStatusSerializer, 
# TimesheetUpdateSerializer, TimesheetListSerializer
class TimesheetCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model=Timesheet
        fields = ['worker','project']  

class TimesheetStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model=ProjectWorker
        fields = ['status','project'] 

class TimesheetUpdateSerializer(serializers.ModelSerializer):
    start_time=serializers.SerializerMethodField()
    end_time=serializers.SerializerMethodField()

    class Meta:
        model = Timesheet
        fields = ['end_time','start_time']
    def get_start_time(self, instance):
        tz = self.context['request'].query_params.get('timezone', None)
        inst=instance.start_time.strftime("%Y-%m-%d %H:%M:%S" )
        inst=datetime.strptime(inst,"%Y-%m-%d %H:%M:%S" )
        l=list(tz)
        if '-' in tz:
            index=l.index('-')
        else:
            index=l.index(' ')
        sign=l[index]
        hours=l[index+1:index+3]
        if hours[0]=='0':
            hours=int(hours[1])
        else:
             hours=int("".join(hours))
        minutes=l[index+4:index+6]
        minutes=int("".join(minutes))
        if sign=='-':
            instance=inst-timedelta(hours=hours,minutes=minutes)
        else :
            instance=inst+timedelta(hours=hours,minutes=minutes)
        return instance.strftime("%Y-%m-%d %H:%M:%S" )
    def get_end_time(self, instance):
        tz = self.context['request'].query_params.get('timezone', None)
        inst=instance.end_time.strftime("%Y-%m-%d %H:%M:%S" )
        inst=datetime.strptime(inst,"%Y-%m-%d %H:%M:%S" )
        l=list(tz)
        if '-' in tz:
            index=l.index('-')
        else:
            index=l.index(' ')
        sign=l[index]
        hours=l[index+1:index+3]
        if hours[0]=='0':
            hours=int(hours[1])
        else:
             hours=int("".join(hours))
        minutes=l[index+4:index+6]
        minutes=int("".join(minutes))
        if sign=='-':
            instance=inst-timedelta(hours=hours,minutes=minutes)
        else :
            instance=inst+timedelta(hours=hours,minutes=minutes)
        return instance.strftime("%Y-%m-%d %H:%M:%S" )
        
class TimesheetListSerializer(serializers.ModelSerializer):
    location=serializers.SerializerMethodField()
    date_added=serializers.SerializerMethodField()
    start_time=serializers.SerializerMethodField()
    end_time=serializers.SerializerMethodField()
    worked_hours=serializers.SerializerMethodField()

    class Meta:
        model = Timesheet
        fields = ['id','date_added','start_time','end_time','location','worked_hours']
    def get_location(self,instance):
        return AddressSerializer(instance.project.address).data
    def get_worked_hours(self, instance):
        l=instance.worked_hours.split(".")
        return (l[0])
    def get_date_added(self, instance):
        tz = self.context['request'].query_params.get('timezone', None)
        inst=instance.date_added.strftime("%Y-%m-%d %H:%M:%S" )
        inst=datetime.strptime(inst,"%Y-%m-%d %H:%M:%S" )
        l=list(tz)
        if '-' in tz:
            index=l.index('-')
        else:
            index=l.index(' ')
        sign=l[index]
        hours=l[index+1:index+3]
        if hours[0]=='0':
            hours=int(hours[1])
        else:
             hours=int("".join(hours))
        minutes=l[index+4:index+6]
        minutes=int("".join(minutes))
        if sign=='-':
            instance=inst-timedelta(hours=hours,minutes=minutes)
        else :
            instance=inst+timedelta(hours=hours,minutes=minutes)
        return instance.strftime("%Y-%m-%d %H:%M:%S" )
    def get_start_time(self, instance):
        tz = self.context['request'].query_params.get('timezone', None)
        inst=instance.start_time.strftime("%Y-%m-%d %H:%M:%S" )
        inst=datetime.strptime(inst,"%Y-%m-%d %H:%M:%S" )
        l=list(tz)
        if '-' in tz:
            index=l.index('-')
        else:
            index=l.index(' ')
        sign=l[index]
        hours=l[index+1:index+3]
        if hours[0]=='0':
            hours=int(hours[1])
        else:
             hours=int("".join(hours))
        minutes=l[index+4:index+6]
        minutes=int("".join(minutes))
        if sign=='-':
            instance=inst-timedelta(hours=hours,minutes=minutes)
        else :
            instance=inst+timedelta(hours=hours,minutes=minutes)
        return instance.strftime("%Y-%m-%d %H:%M:%S" )
    def get_end_time(self, instance):
        tz = self.context['request'].query_params.get('timezone', None)
        inst=instance.end_time.strftime("%Y-%m-%d %H:%M:%S" )
        inst=datetime.strptime(inst,"%Y-%m-%d %H:%M:%S" )
        l=list(tz)
        if '-' in tz:
            index=l.index('-')
        else:
            index=l.index(' ')
        sign=l[index]
        hours=l[index+1:index+3]
        if hours[0]=='0':
            hours=int(hours[1])
        else:
             hours=int("".join(hours))
        minutes=l[index+4:index+6]
        minutes=int("".join(minutes))
        if sign=='-':
            instance=inst-timedelta(hours=hours,minutes=minutes)
        else :
            instance=inst+timedelta(hours=hours,minutes=minutes)
        return instance.strftime("%Y-%m-%d %H:%M:%S" )
