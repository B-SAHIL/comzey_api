from django.urls import include, path
from .api import (WebAuthAPIView,UserList,UserDetailView,ProjectList,ProjectDetailView,UserDeleteAPIView  ,DahsboardAPIView ,AdminUpdateProfileView , AdminChangePasswordView,AdminPasswordResetView,ProjectUpdateStatus)


urlpatterns = [
   
   path('login/' ,WebAuthAPIView.as_view() ,name="login"),
   path('all_users/' ,UserList.as_view() ,name="all_users"),
   path('user_details/' ,UserDetailView.as_view() ,name="user_details"),
   path('allproject/' ,ProjectList.as_view() ,name="allproject"),
   path('projects/update-status/', ProjectUpdateStatus.as_view(), name='project_update_status'),
   path('project_details/' ,ProjectDetailView.as_view() ,name="project_details"),
   path('delete-user/<int:pk>/' ,UserDeleteAPIView.as_view() ,name="user-delete"),
   path('retrieve/' ,DahsboardAPIView.as_view() ,name="retrieve"),
   path('update_profile/' ,AdminUpdateProfileView.as_view() ,name="update-profile"),
   path('change_password/' ,AdminChangePasswordView.as_view() ,name="change-password"),
   path('forgot_password/' ,AdminPasswordResetView.as_view() ,name="forgot-password"),
  
   # path('forgot-password/', ForgotPasswordView.as_view(), name='forgot_password'),
   # path('logout/', WebLogoutAPIView.as_view(), name='logout'),
]
