from django import urls
from django.urls import path
from django.urls.conf import include
from rest_framework.routers import DefaultRouter
from projectcomments.api import CommentViewSet

router = DefaultRouter()
router.register('comment',CommentViewSet,basename='comments')

urlpatterns = [
    path('', include(router.urls)),
]