from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.users.models import AdopterProfile, ShelterProfile
from apps.core.models import Animal, Species, AnimalSize, AnimalEnergy, Breed
from apps.matching.services import MatchingService

User = get_user_model()


class MatchingServiceUnitTest(TestCase):

    def setUp(self):
        # 1. Creazione Utente e Profilo Adottante Base
        self.adopter_user = User.objects.create_user(
            username="test_adopter",
            email="adopter@test.com",
            password="Password123!",
            role=User.Role.ADOPTER,
            gdpr_consent=True
        )
        self.adopter_profile = self.adopter_user.adopter_profile
        self.adopter_profile.housing_type = AdopterProfile.HousingType.HOUSE_GARDEN
        self.adopter_profile.garden_sqm = 100
        self.adopter_profile.has_children = False
        self.adopter_profile.has_other_pets = False
        self.adopter_profile.hours_away_from_home = 4
        self.adopter_profile.activity_level = AdopterProfile.ActivityLevel.MODERATE
        self.adopter_profile.experience_level = AdopterProfile.ExperienceLevel.BEGINNER
        self.adopter_profile.save()

        # 2. Creazione Rifugio e Animale Base
        self.shelter_user = User.objects.create_user(
            username="test_shelter",
            email="shelter@test.com",
            password="Password123!",
            role=User.Role.SHELTER,
            gdpr_consent=True
        )
        self.shelter_profile = ShelterProfile.objects.create(
            user=self.shelter_user,
            shelter_name="Rifugio Test",
            tax_code_vat="12345678901",
            official_email="shelter@test.com"
        )
        self.breed = Breed.objects.create(species=Species.DOG, name="Meticcio")

        self.animal = Animal.objects.create(
            shelter=self.shelter_profile,
            name="Max",
            species=Species.DOG,
            breed=self.breed,
            age_years=2,
            age_months=0,
            gender="M",
            size=AnimalSize.MEDIUM,
            energy_level=AnimalEnergy.MEDIUM,
            requires_garden=False,
            max_hours_alone_per_day=6,
            good_with_children=True,
            good_with_dogs=True,
            good_with_cats=True,
            required_experience_level=AdopterProfile.ExperienceLevel.BEGINNER,
            date_entry_shelter="2026-01-01"
        )

    def test_perfect_match_score(self):
        """
        Verifica che un profilo perfettamente compatibile ottenga un punteggio pari a 100.
        """
        score, breakdown = MatchingService.calculate_match_score(self.adopter_profile, self.animal)

        self.assertEqual(score, 100.0)
        self.assertEqual(breakdown['space_score'], 25.0)
        self.assertEqual(breakdown['family_score'], 25.0)
        self.assertEqual(breakdown['lifestyle_score'], 25.0)
        self.assertEqual(breakdown['experience_score'], 25.0)
        self.assertEqual(len(breakdown['penalties']), 0)

    def test_penalties_garden_and_children(self):
        """
        Verifica l'applicazione delle penalità se l'animale richiede un giardino
        o non è adatto ai bambini, ma l'adottante vive in appartamento con bambini.
        """
        # Modifica profilo adottante
        self.adopter_profile.housing_type = AdopterProfile.HousingType.APARTMENT_NO_BALCONY
        self.adopter_profile.garden_sqm = 0
        self.adopter_profile.has_children = True
        self.adopter_profile.save()

        # Modifica requisiti animale
        self.animal.requires_garden = True
        self.animal.good_with_children = False
        self.animal.save()

        score, breakdown = MatchingService.calculate_match_score(self.adopter_profile, self.animal)

        self.assertLess(score, 100.0)
        self.assertIn("L'animale richiede un giardino o uno spazio verde adeguato.", breakdown['penalties'])
        self.assertIn("L'animale non è indicato per nuclei familiari con bambini.", breakdown['penalties'])

    def test_solitude_hours_penalty(self):
        """
        Verifica che le ore di assenza oltre la soglia massima tollerata riducano il punteggio.
        """
        self.adopter_profile.hours_away_from_home = 10  # 10 ore fuori casa
        self.adopter_profile.save()

        self.animal.max_hours_alone_per_day = 4  # Max 4 ore
        self.animal.save()

        score, breakdown = MatchingService.calculate_match_score(self.adopter_profile, self.animal)

        self.assertLess(breakdown['lifestyle_score'], 25.0)
        self.assertTrue(any("Le ore di assenza" in penalty for penalty in breakdown['penalties']))

    def test_ml_feature_preparation(self):
        """
        Verifica la corretta formattazione delle feature nel DataFrame per il modello ML.
        """
        feature_df = MatchingService._prepare_ml_features(self.adopter_profile, self.animal)

        self.assertEqual(feature_df.shape[0], 1)
        self.assertIn('age_months', feature_df.columns)
        self.assertIn('size_encoded', feature_df.columns)
        self.assertEqual(feature_df['age_months'].iloc[0], 24)