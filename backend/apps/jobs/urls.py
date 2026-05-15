from django.urls import path

from .views import JobOfferListCreateView, SaveJobView, UserSavedJobsView


urlpatterns = [
    path("", JobOfferListCreateView.as_view(), name="job-list-create"),
    path("save/<int:job_id>/", SaveJobView.as_view()),
    path("saved/", UserSavedJobsView.as_view()),
]
