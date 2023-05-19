from django import urls
from django.urls import path
from django.urls.conf import include
from rest_framework.routers import DefaultRouter
from projecttasks.api import TaskViewset

router = DefaultRouter()
router.register('task',TaskViewset,basename='tasks')
urlpatterns = [
    path('', include(router.urls)),
]
