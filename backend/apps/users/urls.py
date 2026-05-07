from django.urls import path

from .views import LoginView, MeView, RegisterView


urlpatterns = [
    path("register/", RegisterView.as_view(), name="user-register"),
    path("login/", LoginView.as_view(), name="user-login"),
    path("me/", MeView.as_view(), name="user-me"),
]
