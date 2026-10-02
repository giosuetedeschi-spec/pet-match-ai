from django.urls import path

from apps.core import views

app_name = 'core'

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('animals/<int:animal_id>/images/upload/', views.AnimalImageUploadView.as_view(), name='animal_image_upload'),
    path('images/<int:pk>/', views.AnimalImageDetailView.as_view(), name='animal_image_detail'),
    path('images/<int:pk>/set-primary/', views.SetPrimaryImageView.as_view(), name='animal_image_set_primary'),
    path('shelter/animals/', views.ShelterAnimalListCreateAPIView.as_view(), name='shelter_animal_list_create'),
    path('shelter/animals/<int:pk>/publish/', views.ShelterAnimalPublishAPIView.as_view(), name='shelter_animal_publish'),
    path('shelter/animals/<int:pk>/', views.ShelterAnimalDetailAPIView.as_view(), name='shelter_animal_detail'),
    path('shelter/applications/', views.ShelterApplicationListAPIView.as_view(), name='shelter_application_list'),
    path('shelter/applications/<int:pk>/', views.ShelterApplicationDetailAPIView.as_view(), name='shelter_application_detail'),
    path('shelter/applications/<int:application_id>/schedule-visit/', views.ScheduleHomeVisitAPIView.as_view(), name='shelter_schedule_visit'),
    path('shelter/dashboard/stats/', views.ShelterDashboardStatsAPIView.as_view(), name='shelter_dashboard_stats'),
    path('catalog/animals/', views.PublicAnimalCatalogAPIView.as_view(), name='public_animal_catalog'),
    path('catalog/animals/<int:pk>/', views.PublicAnimalDetailAPIView.as_view(), name='public_animal_detail'),
    path('animals/<int:animal_id>/apply/', views.AdoptionApplicationCreateAPIView.as_view(), name='animal_apply'),
    path('user/applications/', views.AdopterApplicationListAPIView.as_view(), name='adopter_application_list'),
    path('user/applications/<int:pk>/', views.AdopterApplicationDetailAPIView.as_view(), name='adopter_application_detail'),
    path('user/applications/<int:pk>/withdraw/', views.AdopterApplicationWithdrawAPIView.as_view(), name='adopter_application_withdraw'),
]
