from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from django.utils import timezone
from apps.users.serializers import (
    UserSerializer,
    RegisterSerializer,
    AdopterProfileSerializer,
    ShelterProfileSerializer,
    GDPRConsentUpdateSerializer
)
from apps.audit.models import GDPRConsentLog

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (permissions.AllowAny,)
    serializer_class = RegisterSerializer


class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self):
        return self.request.user


class UpdateAdopterProfileView(generics.UpdateAPIView):
    serializer_class = AdopterProfileSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self):
        return self.request.user.adopter_profile


class UpdateShelterProfileView(generics.UpdateAPIView):
    serializer_class = ShelterProfileSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self):
        return self.request.user.shelter_profile


class GDPRConsentView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        serializer = GDPRConsentUpdateSerializer(data=request.data)
        if serializer.is_valid():
            consent_type = serializer.validated_data['consent_type']
            granted = serializer.validated_data['granted']
            user = request.user

            if consent_type == 'PRIVACY':
                user.gdpr_consent = granted
                user.gdpr_consent_date = timezone.now() if granted else None
            elif consent_type == 'MARKETING':
                user.marketing_consent = granted
            
            user.save()

            # Tracciamento Audit GDPR
            ip_addr = request.META.get('REMOTE_ADDR')
            user_agent = request.META.get('HTTP_USER_AGENT', '')

            GDPRConsentLog.objects.create(
                user=user,
                consent_type=consent_type,
                granted=granted,
                ip_address=ip_addr,
                user_agent=user_agent
            )

            return Response(
                {"detail": "Consenso aggiornato con successo e registrato nei log di audit."},
                status=status.HTTP_200_OK
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework import permissions, status
from apps.users.services import GDPRExportService


class GDPRExportDataAPIView(APIView):
    """
    API (Art. 20 GDPR): Genera ed eroga il file ZIP scaricabile contenente
    tutti i dati personali e lo storico delle attività dell'utente autenticato.
    """
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        user = request.user
        
        # Generazione archivio ZIP in memoria
        zip_content = GDPRExportService.generate_zip_export(user)
        
        filename = f"gdpr_export_{user.username}.zip"
        
        response = HttpResponse(zip_content, content_type='application/zip')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        response['Content-Length'] = len(zip_content)
        
        return response



from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response

from apps.users.serializers import AccountDeletionSerializer
from apps.users.services import GDPRAnonymizationService


class GDPRDeleteAccountAPIView(APIView):
    """
    API (Art. 17 GDPR): Anonimizza in modo irreversibile i dati dell'utente
    e disattiva permanentemente l'account (Diritto all'Oblio).
    """
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        serializer = AccountDeletionSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = request.user
            GDPRAnonymizationService.anonymize_and_delete_user(user, request=request)
            
            return Response(
                {"detail": "Il tuo account e i tuoi dati personali sono stati anonimizzati ed eliminati con successo in conformità al GDPR."},
                status=status.HTTP_200_OK
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)