from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    class Role(models.TextChoices):
        ADOPTER = 'ADOPTER', _('Adottante')
        SHELTER = 'SHELTER', _('Rifugio / Canile')
        ADMIN = 'ADMIN', _('Amministratore')

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.ADOPTER,
        verbose_name=_('Ruolo')
    )
    phone_number = models.CharField(max_length=20, blank=True, verbose_name=_('Numero di Telefono'))
    address = models.CharField(max_length=255, blank=True, verbose_name=_('Indirizzo'))
    city = models.CharField(max_length=100, blank=True, verbose_name=_('Città'))
    province = models.CharField(max_length=10, blank=True, verbose_name=_('Provincia'))
    postal_code = models.CharField(max_length=10, blank=True, verbose_name=_('CAP'))
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True, verbose_name=_('Foto Profilo'))

    # Consensi Privacy & GDPR
    gdpr_consent = models.BooleanField(default=False, verbose_name=_('Consenso Privacy GDPR'))
    gdpr_consent_date = models.DateTimeField(null=True, blank=True, verbose_name=_('Data Consenso GDPR'))
    marketing_consent = models.BooleanField(default=False, verbose_name=_('Consenso Marketing'))

    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Data Registrazione'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Data Aggiornamento'))

    class Meta:
        verbose_name = _('Utente')
        verbose_name_plural = _('Utenti')

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"


class AdopterProfile(models.Model):
    class HousingType(models.TextChoices):
        APARTMENT_NO_BALCONY = 'APARTMENT_NO_BALCONY', _('Appartamento senza balcone')
        APARTMENT_BALCONY = 'APARTMENT_BALCONY', _('Appartamento con balcone/terrazzo')
        HOUSE_GARDEN = 'HOUSE_GARDEN', _('Casa indipendente con giardino')
        VILLA_PARK = 'VILLA_PARK', _('Villa / Casale con terreno')

    class ActivityLevel(models.TextChoices):
        SEDENTARY = 'SEDENTARY', _('Sedentario')
        MODERATE = 'MODERATE', _('Moderatamente attivo')
        ACTIVE = 'ACTIVE', _('Molto attivo / Sportivo')

    class ExperienceLevel(models.TextChoices):
        BEGINNER = 'BEGINNER', _('Prima esperienza')
        INTERMEDIATE = 'INTERMEDIATE', _('Esperienza intermedia')
        EXPERT = 'EXPERT', _('Esperto / Educatore Cinofilo')

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='adopter_profile',
        verbose_name=_('Utente')
    )
    housing_type = models.CharField(
        max_length=30,
        choices=HousingType.choices,
        default=HousingType.APARTMENT_BALCONY,
        verbose_name=_('Tipologia Abitazione')
    )
    garden_sqm = models.PositiveIntegerField(default=0, verbose_name=_('Superficie Giardino (mq)'))
    family_members_count = models.PositiveIntegerField(default=1, verbose_name=_('Componenti Nucleo Familiare'))
    has_children = models.BooleanField(default=False, verbose_name=_('Presenza Bambini'))
    children_ages_info = models.CharField(max_length=200, blank=True, verbose_name=_('Età Bambini'))
    has_other_pets = models.BooleanField(default=False, verbose_name=_('Presenza Altri Animali'))
    other_pets_details = models.TextField(blank=True, verbose_name=_('Dettagli Altri Animali in Casa'))
    hours_away_from_home = models.PositiveIntegerField(default=4, verbose_name=_('Ore fuori casa al giorno'))
    activity_level = models.CharField(
        max_length=20,
        choices=ActivityLevel.choices,
        default=ActivityLevel.MODERATE,
        verbose_name=_('Livello Attività Fisica')
    )
    experience_level = models.CharField(
        max_length=20,
        choices=ExperienceLevel.choices,
        default=ExperienceLevel.BEGINNER,
        verbose_name=_('Livello Esperienza')
    )
    monthly_budget_approx = models.DecimalField(
        max_digits=8, decimal_places=2, default=100.00, verbose_name=_('Budget Mensile Mantenimento (€)')
    )
    preferred_species = models.CharField(max_length=20, default='DOG', verbose_name=_('Specie Preferita'))
    preferred_age_min_months = models.PositiveIntegerField(default=0, verbose_name=_('Età Minima Preferita (mesi)'))
    preferred_age_max_months = models.PositiveIntegerField(default=240, verbose_name=_('Età Massima Preferita (mesi)'))

    class Meta:
        verbose_name = _('Profilo Adottante')
        verbose_name_plural = _('Profili Adottanti')

    def __str__(self):
        return f"Profilo Adottante: {self.user.get_full_name() or self.user.username}"


class ShelterProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='shelter_profile',
        verbose_name=_('Utente Gestore')
    )
    shelter_name = models.CharField(max_length=255, verbose_name=_('Nome Struttura / Rifugio'))
    tax_code_vat = models.CharField(max_length=30, verbose_name=_('Codice Fiscale / Partita IVA'))
    official_email = models.EmailField(verbose_name=_('Email Ufficiale Struttura'))
    website_url = models.URLField(blank=True, verbose_name=_('Sito Web'))
    description = models.TextField(blank=True, verbose_name=_('Descrizione Rifugio'))
    capacity_total = models.PositiveIntegerField(default=50, verbose_name=_('Capienza Totale Ospiti'))
    is_verified = models.BooleanField(default=False, verbose_name=_('Struttura Verificata'))
    verification_date = models.DateTimeField(null=True, blank=True, verbose_name=_('Data Verifica Approval'))

    class Meta:
        verbose_name = _('Profilo Rifugio')
        verbose_name_plural = _('Profili Rifugi')

    def __str__(self):
        return f"{self.shelter_name} ({self.user.city})"