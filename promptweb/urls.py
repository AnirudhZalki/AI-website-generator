"""
URL configuration for promptweb project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
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
from generator import views
from django.urls import path
from generator import views

urlpatterns = [
    path('', views.home, name='home'),
    path('preview/', views.preview, name='preview'),
    path('download/', views.download_project, name='download'),
    path('download/<str:project_id>/', views.download_project, name='download_project'),
    path('convert-to-fullstack/', views.convert_static_to_fullstack_view, name='convert_to_fullstack'),
    path('project/<str:project_id>/files/', views.view_project_files, name='project_files'),
]


# Main urls.py (project level)
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('generator.urls')),  # or whatever your app name is
]
"""
