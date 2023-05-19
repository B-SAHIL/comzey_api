from django import urls
from django.urls import path
from django.urls.conf import include
from rest_framework.routers import DefaultRouter
from api.api import  ProjectViewset, ClientViewSet

router= DefaultRouter()
router = DefaultRouter()
router.register('project',ProjectViewset,basename='projects')
router.register('client',ClientViewSet,basename='clients')
urlpatterns = [
    path('', include(router.urls)),
]
