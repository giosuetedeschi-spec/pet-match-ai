from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from apps.users.models import AdopterProfile, ShelterProfile
from apps.core.models import Animal, AnimalStatus, Species, Breed, AnimalSize, AnimalEnergy

User = get_user_model()


class MatchingAPITestCase(APITestCase):

    def setUp(self):
        # Utente Adottante
        self.adopter = User.objects.create_user(
            username="adopter_user",
            email="adopter@test.com",
            password="Password123!",
            role=User.Role.ADOPTER,
            gdpr_consent=True
        )
        AdopterProfile.objects.create(user=self.adopter)

        # Utente Rifugio
        self.shelter_user = User.objects.create_user(
            username="shelter_user",
            email="shelter@test.com",
            password="Password123!",
            role=User.Role.SHELTER,
            gdpr_consent=True
        )
        self.shelter = ShelterProfile.objects.create(
            user=self.shelter_user,
            shelter_name="Rifugio Milano",
            tax_code_vat="98765432109",
            official_email="shelter@test.com",
            is_verified=True,
        )
        self.breed = Breed.objects.create(species=Species.DOG, name="Golden Retriever")

        self.animal = Animal.objects.create(
            shelter=self.shelter,
            name="Rocky",
            species=Species.DOG,
            breed=self.breed,
            age_years=3,
            size=AnimalSize.LARGE,
            energy_level=AnimalEnergy.HIGH,
            date_entry_shelter="2026-01-01",
            status=AnimalStatus.AVAILABLE,
        )

        self.url = reverse('matching:adopter_recommendations')
        self.preview_url = reverse('matching:matching_preview')

    def _preview(self, **changes):
        payload = {
            "housing_type": AdopterProfile.HousingType.HOUSE_GARDEN,
            "garden_sqm": 50,
            "has_children": False,
            "has_other_pets": False,
            "has_dogs": False,
            "has_cats": False,
            "hours_away_from_home": 4,
            "activity_level": AdopterProfile.ActivityLevel.MODERATE,
            "experience_level": AdopterProfile.ExperienceLevel.BEGINNER,
            "preferred_species": "ANY",
            "preferred_age_min_months": 0,
            "preferred_age_max_months": 360,
        }
        payload.update(changes)
        return self.client.post(self.preview_url, payload, format="json")

    def test_unauthenticated_access_denied(self):
        """
        Verifica che una richiesta non autenticata venga rifiutata con 401 Unauthorized.
        """
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_shelter_role_access_forbidden(self):
        """
        Verifica che un utente con ruolo SHELTER non possa richiedere raccomandazioni adottante (403 Forbidden).
        """
        self.client.force_authenticate(user=self.shelter_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_adopter_get_recommendations_success(self):
        """
        Verifica il recupero delle raccomandazioni per l'utente adottante autenticato.
        """
        self.client.force_authenticate(user=self.adopter)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        self.assertGreaterEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['animal_name'], "Rocky")
        self.assertIn('overall_score', response.data[0])
        self.assertIn('score_breakdown', response.data[0])

    def test_preview_only_penalizes_pets_of_the_matching_species(self):
        self.animal.good_with_dogs = True
        self.animal.good_with_cats = False
        self.animal.save()

        response = self._preview(has_other_pets=True, has_dogs=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total'], 1)
        self.assertEqual(response.data['results'][0]['score'], 100.0)
        self.assertEqual(response.data['excluded_total'], 0)

    def test_preview_excludes_confirmed_child_incompatibility_with_reason(self):
        self.animal.good_with_children = False
        self.animal.save()

        response = self._preview(has_children=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['results'], [])
        self.assertEqual(response.data['excluded_total'], 1)
        self.assertIn('bambini', response.data['excluded'][0]['reasons'][0])
