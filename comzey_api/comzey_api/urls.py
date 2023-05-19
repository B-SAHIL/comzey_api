"""comzey_api URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('web/', include('web_api.urls')),
    path('accounts/', include('accounts.urls')),
    path('api/', include('api.urls')),
    path('accountspayments/', include('accountspayments.urls')),
    path('projectdocs/', include('projectdocuments.urls')),
    path('projectcomments/', include('projectcomments.urls')),
    path('projecttasks/', include('projecttasks.urls')),
    path('projectplans/', include('projectplans.urls')),
    path('projectdailylogs/', include('projectdailylogs.urls')),
    path('projecttimesheets/', include('projecttimesheets.urls')),
    path('projectnotifications/', include('projectnotifications.urls'))
]
