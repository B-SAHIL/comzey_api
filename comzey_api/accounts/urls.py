from django.urls import path
from django.urls.conf import include
from accounts.api import  InductionAnswersViewset, InductionQuestionsViewset, InviteViewset, OccupationViewset, PasswordResetViewset, ProfileDetailsViewset, RegisterViewset, TokenAuthViewset,ChangePasswordViewset 
from django.contrib.auth.views import PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register('invite',InviteViewset,'invite_apis')
router.register('occupation',OccupationViewset,'occupation_apis')
router.register('password_reset',PasswordResetViewset,'password_reset')
router.register('profiledetails',ProfileDetailsViewset,'profiledetailsapi')
router.register('invitation',InviteViewset,'invite_apis')
router.register('inductionquestion',InductionQuestionsViewset,'inductionquestion')
router.register('inductionresponse',InductionAnswersViewset,'inductionresponse')

urlpatterns = [
    path('register/', RegisterViewset.as_view({'post':'create'})), 
    path('invite/', InviteViewset.as_view({'post':'create'})),
    path('profiledetails/', ProfileDetailsViewset.as_view({'get':'retrieve'})),
    path('changepassword/', ChangePasswordViewset.as_view({'post':'create'})),
    path('token-auth/', TokenAuthViewset.as_view({'post':'create'})),
    path('password_reset/done/', PasswordResetDoneView.as_view(template_name="password_reset_done.html"), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', PasswordResetConfirmView.as_view(template_name="password_reset_confirm.html"), name='password_reset_confirm'),
    path('reset/done/', PasswordResetCompleteView.as_view(template_name="password_reset_complete.html"), name='password_reset_complete'),
    path('',include(router.urls)),
]

    # path('password_reset/', PasswordResetView.as_view(template_name="password_reset_form.html"), name='password_reset'),
    # path('password_reset/', PasswordResetViewset.as_view(), name='password_reset'),
