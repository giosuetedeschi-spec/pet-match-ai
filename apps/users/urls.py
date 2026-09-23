from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from apps.users.views import (
    RegisterView,
    UserProfileView,
    UpdateAdopterProfileView,
    UpdateShelterProfileView,
    GDPRConsentView,
)

app_name = 'users'

urlpatterns = [
    # Rotte Autenticazione JWT
    path('auth/register/', RegisterView.as_view(), name='auth_register'),
    path('auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/token/verify/', TokenVerifyView.as_view(), name='token_verify'),

    # Rotte Profilo Utente
    path('me/', UserProfileView.as_view(), name='user_profile'),
    path('me/profile/adopter/', UpdateAdopterProfileView.as_view(), name='update_adopter_profile'),
    path('me/profile/shelter/', UpdateShelterProfileView.as_view(), name='update_shelter_profile'),
    
    # GDPR Management
    path('me/gdpr-consent/', GDPRConsentView.as_view(), name='update_gdpr_consent'),
]


from django.urls import path
from apps.users.views import (
    GDPRExportDataAPIView,
    # ... le altre viste di autenticazione e profilo ...
)

app_name = 'users'

urlpatterns = [
    # Export Portabilità Dati GDPR Art. 20
    path('me/gdpr-export/', GDPRExportDataAPIView.as_view(), name='gdpr_export'),

    # ... rotte esistenti ...
]


from django.urls import path
from apps.users.views import (
    GDPRDeleteAccountAPIView,
    # ... le altre viste ...
)

app_name = 'users'

urlpatterns = [
    # Diritto all'Oblio GDPR Art. 17
    path('me/gdpr-delete/', GDPRDeleteAccountAPIView.as_view(), name='gdpr_delete'),

    # ... altre rotte ...
]

