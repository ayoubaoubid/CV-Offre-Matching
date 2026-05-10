from django.urls import path
#importation de la vue
from .views import MatchRecommendationsView


urlpatterns = [
    path("recommendations/", MatchRecommendationsView.as_view(), name="match-recommendations"),
]
#route , chemin
