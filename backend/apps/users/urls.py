from django.urls import path

from .views import (
    CompanyProfileView,
    LoginView,
    MeView,
    RecruiterRegisterView,
    RegisterView,
)


urlpatterns = [
    path("register/", RegisterView.as_view(), name="user-register"),
    path("register-recruiter/", RecruiterRegisterView.as_view(), name="recruiter-register"),
    path("login/", LoginView.as_view(), name="user-login"),
    path("me/", MeView.as_view(), name="user-me"),
    path("company-profile/", CompanyProfileView.as_view(), name="company-profile"),
]
