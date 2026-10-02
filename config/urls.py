from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from apps.users.views import PendingShelterListView, ShelterDecisionView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.core.urls')),
    path('users/', include('apps.users.urls')),
    path('api/v1/admin/shelters/pending/', PendingShelterListView.as_view(), name='pending_shelters'),
    path('api/v1/admin/shelters/<int:pk>/<str:decision>/', ShelterDecisionView.as_view(), name='shelter_decision'),
    path('api/v1/users/', include('apps.users.urls', namespace='users_api')),
    path('matching/', include('apps.matching.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
