from django import urls
from django.urls import path
from django.urls.conf import include
from rest_framework.routers import DefaultRouter
from projectplans.api import PlanViewset


router = DefaultRouter()
router.register('plan',PlanViewset,basename='plans')
urlpatterns = [
    path('', include(router.urls)),
]
