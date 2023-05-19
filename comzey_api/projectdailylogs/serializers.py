from rest_framework import serializers
from projectdailylogs.models import Address, Weather, DailyLog

# includes AddressSerializer, WeatherSerializer, DailyLogCreateSerializer, DailyLogListSerializer
class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ['name', 'longitude','latitude']

class WeatherSerializer(serializers.ModelSerializer): 
     class Meta:
        model = Weather
        fields = ['current','maximum','weather_type','icon']

class DailyLogCreateSerializer(serializers.ModelSerializer):
    created_time= serializers.SerializerMethodField()
    updated_time= serializers.SerializerMethodField()
    location=AddressSerializer()
    weather=WeatherSerializer()
    class Meta:
        model=DailyLog
        fields='__all__'
    def get_created_time(self, instance):
        return instance.created_time.strftime("%Y-%m-%d %H:%M:%S" )
    def get_updated_time(self, instance):
        return instance.updated_time.strftime("%Y-%m-%d %H:%M:%S" )
    def create(self, validated_data):
        weather = validated_data.pop('weather')
        weather = WeatherSerializer(data=weather)
        weather.is_valid(raise_exception=True)
        weather = weather.save()
        location = validated_data.pop('location')
        location = AddressSerializer(data=location)
        location.is_valid(raise_exception=True)
        location = location.save()
        validated_data['weather'] = weather
        validated_data['location'] = location
        return super().create(validated_data)
    def update(self, instance, validated_data):
        weather_data = validated_data.pop('weather')
        weather = WeatherSerializer(instance=instance.weather,data=weather_data)
        weather.is_valid(raise_exception=True)
        weather = weather.update(instance=instance.weather,validated_data=weather_data)
        location_data = validated_data.pop('location')
        location = AddressSerializer(instance=instance.location,data=location_data)
        location.is_valid(raise_exception=True)
        location = location.update(instance=instance.location,validated_data=location_data)
        validated_data['weather'] = weather
        validated_data['location'] = location
        return super().update(instance, validated_data)

class DailyLogListSerializer(serializers.ModelSerializer):
    created_time= serializers.SerializerMethodField()
    weather=serializers.SerializerMethodField()
    location=AddressSerializer()
    class Meta:
        model=DailyLog
        fields='__all__'
    def get_created_time(self, instance):
        return instance.created_time.strftime("%Y-%m-%d %H:%M:%S" )
    def get_weather(self, instance):
        return {'id':instance.weather.id,'maximum':instance.weather.maximum,'current':instance.weather.current,'icon':instance.weather.icon,'weather_type':instance.weather.weather_type}
