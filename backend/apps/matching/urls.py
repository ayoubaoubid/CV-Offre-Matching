from django.urls import path
#importation de la vue
from .views import (
    CandidateApplyView,
    CandidateNotificationReadView,
    CandidateNotificationsView,
    MatchRecommendationsView,
    RecruiterApplicationsView,
    RecruiterApplicationStatusView,
)


urlpatterns = [
    path("recommendations/", MatchRecommendationsView.as_view(), name="match-recommendations"),
    path("applications/<int:job_id>/", CandidateApplyView.as_view(), name="candidate-apply"),
    path("notifications/", CandidateNotificationsView.as_view(), name="candidate-notifications"),
    path(
        "notifications/<int:notification_id>/read/",
        CandidateNotificationReadView.as_view(),
        name="candidate-notification-read",
    ),
    path("recruiter/applications/", RecruiterApplicationsView.as_view(), name="recruiter-applications"),
    path(
        "recruiter/applications/<int:application_id>/status/",
        RecruiterApplicationStatusView.as_view(),
        name="recruiter-application-status",
    ),
]
#route , chemin
