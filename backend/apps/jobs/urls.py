from django.urls import path

from .views import (
    JobCandidatesView,
    JobOfferListCreateView,
    RecruiterDashboardView,
    RecruiterJobDetailView,
    RecruiterJobListCreateView,
    RecruiterJobStatusView,
    SaveJobView,
    UserSavedJobsView,
)


urlpatterns = [
    path("", JobOfferListCreateView.as_view(), name="job-list-create"),
    path("recruiter/dashboard/", RecruiterDashboardView.as_view(), name="recruiter-dashboard"),
    path("recruiter/jobs/", RecruiterJobListCreateView.as_view(), name="recruiter-jobs"),
    path("recruiter/jobs/<int:job_id>/", RecruiterJobDetailView.as_view(), name="recruiter-job-detail"),
    path("recruiter/jobs/<int:job_id>/status/", RecruiterJobStatusView.as_view(), name="recruiter-job-status"),
    path("recruiter/jobs/<int:job_id>/candidates/", JobCandidatesView.as_view(), name="recruiter-job-candidates"),
    path("save/<int:job_id>/", SaveJobView.as_view()),
    path("saved/", UserSavedJobsView.as_view()),
]
