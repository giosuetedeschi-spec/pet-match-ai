from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from apps.audit.models import GDPRConsentLog

User = get_user_model()


class AuthAndGDPRAPITestCase(APITestCase):

    def setUp(self):
        self.register_url = reverse('users_api:auth_register')
        self.login_url = reverse('users_api:token_obtain_pair')
        self.gdpr_url = reverse('users_api:update_gdpr_consent')

    def test_user_registration_success(self):
        """
        Verifica la registrazione di un nuovo utente con consenso GDPR obbligatorio.
        """
        payload = {
            "username": "new_user",
            "email": "newuser@example.com",
            "password": "StrongPassword123!",
            "password_confirm": "StrongPassword123!",
            "first_name": "Mario",
            "last_name": "Rossi",
            "role": "ADOPTER",
            "gdpr_consent": True
        }
        response = self.client.post(self.register_url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username="new_user").exists())
        # Verifica la registrazione del log di audit GDPR
        self.assertTrue(GDPRConsentLog.objects.filter(user__username="new_user").exists())

    def test_registration_fails_without_gdpr_consent(self):
        """
        Verifica che la registrazione fallisca se il consenso GDPR è False o mancante.
        """
        payload = {
            "username": "no_gdpr_user",
            "email": "nogdpr@example.com",
            "password": "StrongPassword123!",
            "password_confirm": "StrongPassword123!",
            "gdpr_consent": False
        }
        response = self.client.post(self.register_url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('gdpr_consent', response.data)

    def test_jwt_login_success(self):
        """
        Verifica l'ottenimento dei token JWT (Access e Refresh) a seguito del login.
        """
        user = User.objects.create_user(
            username="login_test",
            password="MySecretPassword123!",
            gdpr_consent=True
        )

        payload = {
            "username": "login_test",
            "password": "MySecretPassword123!"
        }
        response = self.client.post(self.login_url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)