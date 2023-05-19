from django.urls import path
from django.urls.conf import include
from rest_framework.routers import DefaultRouter
from projectdailylogs.api import DailyLogViewset

router = DefaultRouter()
router.register('dailylog',DailyLogViewset,basename='dailylogs')
urlpatterns = [
    path('', include(router.urls)),
]
