from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from apps.users.models import ShelterProfile
from apps.core.models import Animal, Species, Breed, AnimalStatus

User = get_user_model()


class ShelterDashboardAPITestCase(APITestCase):

    def setUp(self):
        self.shelter_user = User.objects.create_user(
            username="shelter_admin",
            email="shelter@test.com",
            password="Password123!",
            role=User.Role.SHELTER,
            gdpr_consent=True
        )
        self.shelter_profile = ShelterProfile.objects.create(
            user=self.shelter_user,
            shelter_name="Rifugio Torino",
            tax_code_vat="11223344556",
            official_email="shelter@test.com"
        )
        self.breed = Breed.objects.create(species=Species.CAT, name="Europeo")

        self.list_create_url = reverse('core:shelter_animal_list_create')
        self.stats_url = reverse('core:shelter_dashboard_stats')

    def test_create_animal_card(self):
        """
        Verifica la creazione di una scheda animale da parte del rifugio autenticato.
        """
        self.client.force_authenticate(user=self.shelter_user)

        payload = {
            "name": "Mino",
            "species": Species.CAT,
            "breed": self.breed.id,
            "age_years": 1,
            "age_months": 2,
            "gender": "M",
            "size": "SMALL",
            "energy_level": "LOW",
            "description": "Gatto tranquillo in cerca di casa.",
            "status": AnimalStatus.AVAILABLE,
            "date_entry_shelter": "2026-02-01"
        }

        response = self.client.post(self.list_create_url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Animal.objects.filter(name="Mino", shelter=self.shelter_profile).exists())

    def test_shelter_dashboard_stats(self):
        """
        Verifica il recupero delle metriche riassuntive per la dashboard.
        """
        self.client.force_authenticate(user=self.shelter_user)
        response = self.client.get(self.stats_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('animals_summary', response.data)
        self.assertIn('applications_summary', response.data)
        self.assertEqual(response.data['shelter_name'], "Rifugio Torino")