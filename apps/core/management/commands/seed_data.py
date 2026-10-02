from datetime import timedelta
from io import BytesIO

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify
from PIL import Image, ImageDraw

from apps.core.models import Animal, AnimalEnergy, AnimalImage, AnimalSize, AnimalStatus, Breed, Species
from apps.users.models import ShelterProfile

User = get_user_model()

SHELTERS = (
    ('rifugio_esperanza', 'Torino', 'TO', '10121', 'RESCUE', 'Piemonte'),
    ('demo_shelter_milano', 'Milano', 'MI', '20121', 'MUNICIPAL_SHELTER', 'Lombardia'),
    ('demo_shelter_roma', 'Roma', 'RM', '00118', 'PRIVATE_SHELTER', 'Lazio'),
    ('demo_shelter_napoli', 'Napoli', 'NA', '80121', 'ASSOCIATION', 'Campania'),
    ('demo_shelter_firenze', 'Firenze', 'FI', '50121', 'CATTERY', 'Toscana'),
    ('demo_shelter_palermo', 'Palermo', 'PA', '90121', 'RESCUE', 'Sicilia'),
)

DOG_BREEDS = ('Meticcio', 'Labrador Retriever', 'Pastore Tedesco', 'Jack Russell Terrier', 'Golden Retriever')
CAT_BREEDS = ('Europeo', 'Siamese', 'Maine Coon')
NAMES = ('Luna', 'Milo', 'Nina', 'Leo', 'Maya', 'Tito', 'Stella', 'Argo', 'Mia', 'Brio', 'Oliva', 'Pippo')


class Command(BaseCommand):
    help = 'Crea un catalogo demo locale, senza credenziali di accesso predefinite.'

    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError('Il seed demo è consentito solo con DEBUG=True.')

        with transaction.atomic():
            breeds = self._seed_breeds()
            shelters = [self._seed_shelter(index, data) for index, data in enumerate(SHELTERS)]
            self._seed_pending_shelter()
            created_animals = self._seed_animals(shelters, breeds)
            self._disable_legacy_seed_admin()

        self.stdout.write(self.style.SUCCESS(
            f'Catalogo demo pronto: {len(shelters)} rifugi approvati, '
            f'{Animal.objects.count()} animali totali, {created_animals} nuovi.'
        ))
        self.stdout.write('Account demo senza password utilizzabile. Crea un admin locale con createsuperuser.')

    def _seed_breeds(self):
        breeds = {}
        for species, names in ((Species.DOG, DOG_BREEDS), (Species.CAT, CAT_BREEDS)):
            for name in names:
                breeds[(species, name)], _ = Breed.objects.get_or_create(species=species, name=name)
        return breeds

    def _seed_user(self, username, city, province, postal_code, address):
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'email': f'{username}@example.test',
                'role': User.Role.SHELTER,
                'address': address,
                'city': city,
                'province': province,
                'postal_code': postal_code,
                'phone_number': '0000000000',
                'gdpr_consent': True,
                'gdpr_consent_date': timezone.now(),
            },
        )
        if created or user.has_usable_password():
            user.set_unusable_password()
            user.save(update_fields=('password',))
        if user.role != User.Role.SHELTER:
            raise CommandError(f'L’utente seed {username} esiste con ruolo incompatibile.')
        return user

    def _seed_shelter(self, index, data):
        username, city, province, postal_code, organization_type, region = data
        user = self._seed_user(username, city, province, postal_code, f'Piazza Demo 1, {city}')
        profile, _ = ShelterProfile.objects.get_or_create(
            user=user,
            defaults={
                'shelter_name': f'Rifugio {city}',
                'legal_name': f'Associazione Demo {city}',
                'organization_type': organization_type,
                'tax_code_vat': f'DEMO-{province}-000{index + 1}',
                'official_email': f'contatti-{province.lower()}@example.test',
                'description': f'Rifugio demo per il catalogo locale in {region}.',
                'is_verified': True,
                'verification_status': ShelterProfile.VerificationStatus.APPROVED,
                'verification_date': timezone.now(),
            },
        )
        if not profile.is_verified or profile.verification_status != ShelterProfile.VerificationStatus.APPROVED:
            profile.is_verified = True
            profile.verification_status = ShelterProfile.VerificationStatus.APPROVED
            profile.verification_date = profile.verification_date or timezone.now()
            profile.save(update_fields=('is_verified', 'verification_status', 'verification_date'))
        return profile

    def _seed_pending_shelter(self):
        user = self._seed_user('demo_shelter_pending', 'Bologna', 'BO', '40121', 'Via Demo 1, Bologna')
        ShelterProfile.objects.get_or_create(
            user=user,
            defaults={
                'shelter_name': 'Rifugio Demo in attesa',
                'legal_name': 'Associazione Demo in attesa',
                'organization_type': ShelterProfile.OrganizationType.ASSOCIATION,
                'tax_code_vat': 'DEMO-BO-0007',
                'official_email': 'contatti-bo@example.test',
                'description': 'Richiesta demo ancora da approvare.',
            },
        )

    def _seed_animals(self, shelters, breeds):
        today = timezone.localdate()
        created_count = 0
        for index in range(120):
            species = Species.DOG if index < 70 else Species.CAT
            shelter = shelters[index % len(shelters)]
            name = f'{NAMES[index % len(NAMES)]} {index + 1:03d}'
            status = self._status_for(index)
            days_in_care = 180 if 20 <= index < 35 else 30 + (index % 150)
            animal, created = Animal.objects.get_or_create(
                shelter=shelter,
                name=name,
                defaults={
                    'species': species,
                    'breed': breeds[(species, (DOG_BREEDS if species == Species.DOG else CAT_BREEDS)[index % (len(DOG_BREEDS) if species == Species.DOG else len(CAT_BREEDS))])],
                    'age_years': index % 12,
                    'age_months': (index * 3) % 12,
                    'gender': 'F' if index % 2 else 'M',
                    'size': tuple(AnimalSize)[index % len(AnimalSize)],
                    'energy_level': tuple(AnimalEnergy)[index % len(AnimalEnergy)],
                    'good_with_cats': index % 3 != 0,
                    'good_with_dogs': index % 4 != 0,
                    'good_with_children': index % 5 != 0,
                    'requires_garden': index % 11 == 0,
                    'is_spayed_neutered': index % 3 != 0,
                    'is_vaccinated': index % 4 != 0,
                    'special_needs': index % 17 == 0,
                    'description': self._description(name, species, index),
                    'status': status,
                    'date_entry_shelter': today - timedelta(days=days_in_care),
                    'date_adopted': today - timedelta(days=10 + index % 120) if status == AnimalStatus.ADOPTED else None,
                },
            )
            if created:
                created_count += 1
            if not animal.images.exists():
                self._add_placeholder_image(animal)
        return created_count

    @staticmethod
    def _status_for(index):
        if index < 10:
            return AnimalStatus.DRAFT
        if index < 18:
            return AnimalStatus.ADOPTED
        if index < 20:
            return AnimalStatus.CARE
        return AnimalStatus.AVAILABLE

    @staticmethod
    def _description(name, species, index):
        animal_type = 'cane' if species == Species.DOG else 'gatto'
        traits = ('curioso', 'affettuoso', 'tranquillo', 'giocherellone')
        return f'{name} è un {animal_type} {traits[index % len(traits)]}, seguito dal rifugio e pronto a conoscere una famiglia.'

    @staticmethod
    def _add_placeholder_image(animal):
        background = '#E8F1ED' if animal.species == Species.DOG else '#F4E9DC'
        accent = '#315C4B' if animal.species == Species.DOG else '#8A5A36'
        image = Image.new('RGB', (800, 560), background)
        draw = ImageDraw.Draw(image)
        draw.rounded_rectangle((48, 48, 752, 512), radius=36, fill='#FFFFFF')
        draw.ellipse((290, 135, 510, 355), fill=accent)
        draw.polygon(((320, 175), (305, 95), (380, 155)), fill=accent)
        draw.polygon(((420, 155), (495, 95), (475, 180)), fill=accent)
        label = 'CANE' if animal.species == Species.DOG else 'GATTO'
        draw.text((350, 400), label, fill=accent, anchor='mm')
        buffer = BytesIO()
        image.save(buffer, format='PNG')
        image_name = f'demo/{animal.pk}-{slugify(animal.name)}.png'
        AnimalImage.objects.create(
            animal=animal,
            image=ContentFile(buffer.getvalue(), name=image_name),
            caption=f'Immagine segnaposto locale: {animal.name}',
            is_primary=True,
        )

    @staticmethod
    def _disable_legacy_seed_admin():
        legacy = User.objects.filter(username='admin', email='admin@example.com', role=User.Role.ADMIN).first()
        if legacy and legacy.has_usable_password():
            legacy.set_unusable_password()
            legacy.save(update_fields=('password',))
