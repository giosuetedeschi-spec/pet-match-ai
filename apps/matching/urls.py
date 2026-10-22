from django.urls import path
from apps.matching.views import AdopterRecommendationsAPIView, MatchingPreviewAPIView

app_name = 'matching'

urlpatterns = [
    path('recommendations/', AdopterRecommendationsAPIView.as_view(), name='adopter_recommendations'),
    path('preview/', MatchingPreviewAPIView.as_view(), name='matching_preview'),
]
