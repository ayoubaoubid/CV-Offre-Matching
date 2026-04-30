from django.urls import path
from .views import TestConnectionView

urlpatterns = [
    # Route de test (à supprimer plus tard si vous voulez)
    path('test-connection/', TestConnectionView.as_view(), name='test-connection'),
    
    # Exemple d'ajout de route plus tard :
    # path('profile/', views.UserProfileView.as_view(), name='user-profile'),
]
