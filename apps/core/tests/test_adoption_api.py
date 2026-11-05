from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.core.models import Animal, AnimalStatus, Breed, Species, AdoptionApplication
from apps.users.models import AdopterProfile, ShelterProfile


User = get_user_model()


class AdoptionApplicationVisibilityTest(APITestCase):
    def test_adopter_cannot_apply_for_available_animal_from_unverified_shelter(self):
        adopter = User.objects.create_user(
            username="adopter",
            email="adopter@example.test",
            password="Password123!",
            role=User.Role.ADOPTER,
            gdpr_consent=True,
        )
        AdopterProfile.objects.create(user=adopter)
        shelter_user = User.objects.create_user(
            username="shelter",
            email="shelter@example.test",
            password="Password123!",
            role=User.Role.SHELTER,
            gdpr_consent=True,
        )
        shelter = ShelterProfile.objects.create(
            user=shelter_user,
            shelter_name="Rifugio non verificato",
            tax_code_vat="12345678903",
            official_email="shelter@example.test",
            is_verified=False,
        )
        breed = Breed.objects.create(species=Species.DOG, name="Meticcio")
        animal = Animal.objects.create(
            shelter=shelter,
            name="Luna",
            species=Species.DOG,
            breed=breed,
            gender="M",
            description="Cane in cerca di casa.",
            date_entry_shelter="2026-01-01",
            status=AnimalStatus.AVAILABLE,
        )
        self.client.force_authenticate(user=adopter)

        response = self.client.post(reverse("core:animal_apply", args=[animal.id]), {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(AdoptionApplication.objects.filter(adopter=adopter, animal=animal).exists())
