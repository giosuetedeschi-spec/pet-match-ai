from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.core.models import Species, Breed, Animal, AnimalSize, AnimalEnergy, AnimalStatus
from apps.users.models import ShelterProfile, AdopterProfile

User = get_user_model()


class Command(BaseCommand):
    help = 'Popola il database con dati iniziali di test e razze predefinite'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING('Inizio popolamento dati di base...'))

        # 1. Creazione Superuser Amministratore
        admin_email = "admin@example.com"
        if not User.objects.filter(username="admin").exists():
            admin = User.objects.create_superuser(
                username="admin",
                email=admin_email,
                password="AdminPassword123!",
                role=User.Role.ADMIN,
                gdpr_consent=True
            )
            self.stdout.write(self.style.SUCCESS(f'Superuser creato: admin / AdminPassword123!'))

        # 2. Popolamento Razze Principali (Cani e Gatti)
        breeds_data = [
            (Species.DOG, 'Meticcio'),
            (Species.DOG, 'Labrador Retriever'),
            (Species.DOG, 'Pastore Tedesco'),
            (Species.DOG, 'Jack Russell Terrier'),
            (Species.DOG, 'Golden Retriever'),
            (Species.CAT, 'Europeo'),
            (Species.CAT, 'Siamese'),
            (Species.CAT, 'Maine Coon'),
        ]

        for species, name in breeds_data:
            Breed.objects.get_or_create(species=species, name=name)

        self.stdout.write(self.style.SUCCESS(f'Inserite {len(breeds_data)} razze di base.'))

        # 3. Creazione Rifugio Demo
        shelter_user, created = User.objects.get_or_create(
            username="rifugio_esperanza",
            email="info@esperanza.org",
            defaults={
                'role': User.Role.SHELTER,
                'city': 'Torino',
                'province': 'TO',
                'gdpr_consent': True
            }
        )
        if created:
            shelter_user.set_password("RifugioPass123!")
            shelter_user.save()

        shelter_profile, _ = ShelterProfile.objects.get_or_create(
            user=shelter_user,
            defaults={
                'shelter_name': 'Rifugio Esperanza Torino',
                'tax_code_vat': '12345678901',
                'official_email': 'info@esperanza.org',
                'is_verified': True
            }
        )

        # 4. Creazione Animale Demo
        breed_meticcio = Breed.objects.filter(name='Meticcio').first()
        animal, animal_created = Animal.objects.get_or_create(
            name="Luna",
            shelter=shelter_profile,
            defaults={
                'species': Species.DOG,
                'breed': breed_meticcio,
                'age_years': 2,
                'age_months': 3,
                'gender': 'F',
                'size': AnimalSize.MEDIUM,
                'energy_level': AnimalEnergy.MEDIUM,
                'good_with_children': True,
                'good_with_dogs': True,
                'good_with_cats': True,
                'requires_garden': False,
                'max_hours_alone_per_day': 6,
                'description': 'Luna è una cagnolina dolce e affettuosa, cerca una famiglia con cui fare passeggiate.',
                'status': AnimalStatus.AVAILABLE,
                'date_entry_shelter': '2026-01-15'
            }
        )

        if animal_created:
            self.stdout.write(self.style.SUCCESS(f'Creato animale demo: {animal.name}'))

        self.stdout.write(self.style.SUCCESS('Seeding completato con successo!'))