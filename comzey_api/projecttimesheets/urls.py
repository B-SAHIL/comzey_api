from django import urls
from django.urls import path
from django.urls.conf import include
from rest_framework.routers import DefaultRouter
from projecttimesheets.api import  TimesheetViewset

router = DefaultRouter()
router.register('timesheet',TimesheetViewset,basename='timesheets')
urlpatterns = [
    path('', include(router.urls)),
]
