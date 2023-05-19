from django.urls import path
from django.urls.conf import include
from rest_framework.routers import DefaultRouter
from projectnotifications.api import   ContentViewset, FCMViewset

router = DefaultRouter()
router.register('fcm',FCMViewset,basename='notifications')
router.register('content',ContentViewset ,basename='privacyPolicy')
urlpatterns = [
    path('', include(router.urls)),
]
