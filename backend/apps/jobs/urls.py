from django.urls import path

from .views import JobOfferListCreateView


urlpatterns = [
    path("", JobOfferListCreateView.as_view(), name="job-list-create"),
]
