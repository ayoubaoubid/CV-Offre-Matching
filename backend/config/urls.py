from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path
from rest_framework.routers import DefaultRouter


router = DefaultRouter()


def ping_view(request):
    return JsonResponse(
        {
            "status": "success",
            "message": "Backend et frontend sont connectes avec succes.",
        }
    )


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/ping/", ping_view, name="ping"),
    path("api/users/", include("apps.users.urls")),
    path("api/jobs/", include("apps.jobs.urls")),
    path("api/matching/", include("apps.matching.urls")),
    path("api/v1/", include(router.urls)),
]
