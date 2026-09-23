from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
]

from django.urls import path
from apps.core.views import (
    AnimalImageUploadView,
    AnimalImageDetailView,
    SetPrimaryImageView
)

app_name = 'core'

urlpatterns = [
    path('animals/<int:animal_id>/images/upload/', AnimalImageUploadView.as_view(), name='animal_image_upload'),
    path('images/<int:pk>/', AnimalImageDetailView.as_view(), name='animal_image_detail'),
    path('images/<int:pk>/set-primary/', SetPrimaryImageView.as_view(), name='animal_image_set_primary'),
]

from django.urls import path
from apps.core.views import (
    AnimalImageUploadView,
    AnimalImageDetailView,
    SetPrimaryImageView,
    ShelterAnimalListCreateAPIView,
    ShelterAnimalDetailAPIView,
    ShelterApplicationListAPIView,
    ShelterApplicationDetailAPIView,
    ScheduleHomeVisitAPIView,
    ShelterDashboardStatsAPIView
)

app_name = 'core'

urlpatterns = [
    # Rotte Gestione Immagini Media
    path('animals/<int:animal_id>/images/upload/', AnimalImageUploadView.as_view(), name='animal_image_upload'),
    path('images/<int:pk>/', AnimalImageDetailView.as_view(), name='animal_image_detail'),
    path('images/<int:pk>/set-primary/', SetPrimaryImageView.as_view(), name='animal_image_set_primary'),

    # Rotte Dashboard Rifugio - Schede Animali (CRUD)
    path('shelter/animals/', ShelterAnimalListCreateAPIView.as_view(), name='shelter_animal_list_create'),
    path('shelter/animals/<int:pk>/', ShelterAnimalDetailAPIView.as_view(), name='shelter_animal_detail'),

    # Rotte Dashboard Rifugio - Candidature e Visite Pre-Affido
    path('shelter/applications/', ShelterApplicationListAPIView.as_view(), name='shelter_application_list'),
    path('shelter/applications/<int:pk>/', ShelterApplicationDetailAPIView.as_view(), name='shelter_application_detail'),
    path('shelter/applications/<int:application_id>/schedule-visit/', ScheduleHomeVisitAPIView.as_view(), name='shelter_schedule_visit'),

    # Rotte Dashboard Rifugio - Analytics e Statistiche
    path('shelter/dashboard/stats/', ShelterDashboardStatsAPIView.as_view(), name='shelter_dashboard_stats'),
]

from django.urls import path
from apps.core.views import (
    PublicAnimalCatalogAPIView,
    PublicAnimalDetailAPIView,
    # ... le altre viste già presenti ...
)

app_name = 'core'

urlpatterns = [
    # Catalogo Pubblico Animali
    path('catalog/animals/', PublicAnimalCatalogAPIView.as_view(), name='public_animal_catalog'),
    path('catalog/animals/<int:pk>/', PublicAnimalDetailAPIView.as_view(), name='public_animal_detail'),

    # ... rotte media e dashboard rifugio ...
]