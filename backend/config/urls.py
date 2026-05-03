"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
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
from django.urls import path, include
from django.http import JsonResponse
from rest_framework.routers import DefaultRouter

# Création du routeur principal de DRF
router = DefaultRouter()
# Exemple: router.register(r'jobs', JobViewSet)

def ping_view(request):
    return JsonResponse({"status": "success", "message": "Backend et Frontend sont connectés avec succès !"})

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Endpoint de base
    path('api/ping/', ping_view, name='ping'),
    
    # Routeur DRF pour les futures API CRUD
    path('api/v1/', include(router.urls)),
    
    # URLs spécifiques aux applications
    path('api/users/', include('apps.users.urls')),
    path('api/jobs/', include('apps.jobs.urls')),
    path('api/matching/', include('apps.matching.urls')),
]
