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