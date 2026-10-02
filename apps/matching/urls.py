from django.urls import path
from apps.matching.views import AdopterRecommendationsAPIView

app_name = 'matching'

urlpatterns = [
    path('recommendations/', AdopterRecommendationsAPIView.as_view(), name='adopter_recommendations'),
]