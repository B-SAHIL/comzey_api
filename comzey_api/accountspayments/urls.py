from django.urls import path
from django.urls.conf import include
from accountspayments.api import ProductViewset,PlansViewset,SubscriptionViewset,PaymentViewset
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register('product',ProductViewset,'paypalproducts_apis')
router.register('plan',PlansViewset,'paypalplans_apis')
router.register('subscription',SubscriptionViewset,'paypalsubscription_apis')
router.register('payment',PaymentViewset,'paypalpayment_apis')

urlpatterns = [
    path('subscription/details/', SubscriptionViewset.as_view({'get':'retrieve'})),
    path('subscription/', SubscriptionViewset.as_view({'post':'create'})),
    path('',include(router.urls)),
]
