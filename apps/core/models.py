from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.users.models import User, ShelterProfile, AdopterProfile


class Species(models.TextChoices):
    DOG = 'DOG', _('Cane')
    CAT = 'CAT', _('Gatto')
    OTHER = 'OTHER', _('Altro')


class AnimalSize(models.TextChoices):
    SMALL = 'SMALL', _('Piccola (fino a 10kg)')
    MEDIUM = 'MEDIUM', _('Media (10-25kg)')
    LARGE = 'LARGE', _('Grande (25-45kg)')
    GIANT = 'GIANT', _('Gigante (oltre 45kg)')


class AnimalEnergy(models.TextChoices):
    LOW = 'LOW', _('Basso (Tranquillo / Anziano)')
    MEDIUM = 'MEDIUM', _('Medio (Passeggiate regolari)')
    HIGH = 'HIGH', _('Alto (Molto energico)')
    VERY_HIGH = 'VERY_HIGH', _('Molto Alto (Lavoro / Sport)')


class AnimalStatus(models.TextChoices):
    AVAILABLE = 'AVAILABLE', _('Disponibile per adozione')
    PENDING = 'PENDING', _('Richiesta in corso')
    ADOPTED = 'ADOPTED', _('Adottato')
    CARE = 'CARE', _('In cure mediche / Stallo')
    ARCHIVED = 'ARCHIVED', _('Archiviato')


class Breed(models.Model):
    species = models.CharField(max_length=10, choices=Species.choices, default=Species.DOG, verbose_name=_('Specie'))
    name = models.CharField(max_length=100, verbose_name=_('Nome Razza'))
    description = models.TextField(blank=True, verbose_name=_('Descrizione Razza'))

    class Meta:
        verbose_name = _('Razza')
        verbose_name_plural = _('Razze')
        ordering = ['species', 'name']

    def __str__(self):
        return f"{self.get_species_display()} - {self.name}"


class Animal(models.Model):
    shelter = models.ForeignKey(
        ShelterProfile,
        on_delete=models.CASCADE,
        related_name='animals',
        verbose_name=_('Rifugio di Appartenenza')
    )
    name = models.CharField(max_length=100, verbose_name=_('Nome Animale'))
    species = models.CharField(max_length=10, choices=Species.choices, default=Species.DOG, verbose_name=_('Specie'))
    breed = models.ForeignKey(
        Breed,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='animals',
        verbose_name=_('Razza')
    )
    age_years = models.PositiveIntegerField(default=0, verbose_name=_('Età (Anni)'))
    age_months = models.PositiveIntegerField(default=0, verbose_name=_('Età (Mesi)'))
    gender = models.CharField(
        max_length=10,
        choices=[('M', _('Maschio')), ('F', _('Femmina'))],
        verbose_name=_('Sesso')
    )
    size = models.CharField(max_length=10, choices=AnimalSize.choices, default=AnimalSize.MEDIUM, verbose_name=_('Taglia'))
    energy_level = models.CharField(max_length=15, choices=AnimalEnergy.choices, default=AnimalEnergy.MEDIUM, verbose_name=_('Livello Energia'))

    # Requisiti e Compatibilità
    good_with_cats = models.BooleanField(null=True, blank=True, verbose_name=_('Compatibile con Gatti'))
    good_with_dogs = models.BooleanField(null=True, blank=True, verbose_name=_('Compatibile con Cani'))
    good_with_children = models.BooleanField(null=True, blank=True, verbose_name=_('Compatibile con Bambini'))
    requires_garden = models.BooleanField(default=False, verbose_name=_('Giardino Obbligatorio'))
    max_hours_alone_per_day = models.PositiveIntegerField(default=6, verbose_name=_('Ore Max Solitudine al Giorno'))
    required_experience_level = models.CharField(
        max_length=20,
        choices=AdopterProfile.ExperienceLevel.choices,
        default=AdopterProfile.ExperienceLevel.BEGINNER,
        verbose_name=_('Livello Esperienza Richiesto Adottante')
    )

    # Dati Sanitari
    is_spayed_neutered = models.BooleanField(default=False, verbose_name=_('Sterilizzato / Castrato'))
    is_vaccinated = models.BooleanField(default=False, verbose_name=_('Vaccinato'))
    is_microchipped = models.BooleanField(default=True, verbose_name=_('Microchippato'))
    microchip_code = models.CharField(max_length=50, blank=True, verbose_name=_('Codice Microchip'))
    special_needs = models.BooleanField(default=False, verbose_name=_('Bisogni Speciali / Cure Continuative'))
    health_notes = models.TextField(blank=True, verbose_name=_('Note Cliniche / Sanitarie'))

    description = models.TextField(verbose_name=_('Descrizione e Carattere'))
    status = models.CharField(
        max_length=15,
        choices=AnimalStatus.choices,
        default=AnimalStatus.AVAILABLE,
        verbose_name=_('Stato Adozione')
    )

    date_entry_shelter = models.DateField(verbose_name=_('Data Ingresso in Rifugio'))
    date_adopted = models.DateField(null=True, blank=True, verbose_name=_('Data Adozione'))

    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Data Creazione Scheda'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Data Ultima Modifica'))

    class Meta:
        verbose_name = _('Animale')
        verbose_name_plural = _('Animali')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.get_species_display()} - {self.shelter.shelter_name})"

    @property
    def total_age_in_months(self):
        return (self.age_years * 12) + self.age_months


class AnimalImage(models.Model):
    animal = models.ForeignKey(
        Animal,
        on_delete=models.CASCADE,
        related_name='images',
        verbose_name=_('Animale')
    )
    image = models.ImageField(upload_to='animals/', verbose_name=_('File Immagine'))
    caption = models.CharField(max_length=150, blank=True, verbose_name=_('Didascalia'))
    is_primary = models.BooleanField(default=False, verbose_name=_('Foto Copertina'))
    order = models.PositiveIntegerField(default=0, verbose_name=_('Ordine Ordinamento'))

    class Meta:
        verbose_name = _('Immagine Animale')
        verbose_name_plural = _('Immagini Animali')
        ordering = ['order', '-is_primary', 'id']

    def __str__(self):
        return f"Immagine {self.animal.name}"


class ApplicationStatus(models.TextChoices):
    SUBMITTED = 'SUBMITTED', _('Inviata')
    IN_REVIEW = 'IN_REVIEW', _('In Valutazione dal Rifugio')
    HOME_VISIT = 'HOME_VISIT', _('Visita Pre-Affido Programmata')
    APPROVED = 'APPROVED', _('Approvata')
    REJECTED = 'REJECTED', _('Rifiutata')
    WITHDRAWN = 'WITHDRAWN', _('Ritirata dall\'Utente')


class AdoptionApplication(models.Model):
    adopter = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='applications',
        verbose_name=_('Candidato Adottante')
    )
    animal = models.ForeignKey(
        Animal,
        on_delete=models.CASCADE,
        related_name='applications',
        verbose_name=_('Animale Richiesto')
    )
    status = models.CharField(
        max_length=20,
        choices=ApplicationStatus.choices,
        default=ApplicationStatus.SUBMITTED,
        verbose_name=_('Stato Candidatura')
    )
    motivational_notes = models.TextField(verbose_name=_('Lettera Motivazionale'))
    compatibility_score_at_submission = models.FloatField(
        default=0.0,
        verbose_name=_('Punteggio Compatibilità ML all\'Invio')
    )
    shelter_notes = models.TextField(blank=True, verbose_name=_('Note Interne del Rifugio'))

    submitted_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Data Invio Candidatura'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Data Ultimo Aggiornamento'))

    class Meta:
        verbose_name = _('Domanda di Adozione')
        verbose_name_plural = _('Domande di Adozione')
        ordering = ['-submitted_at']
        unique_together = ('adopter', 'animal')

    def __str__(self):
        return f"Candidatura {self.adopter.username} per {self.animal.name} [{self.get_status_display()}]"


class HomeVisit(models.Model):
    class VisitOutcome(models.TextChoices):
        PENDING = 'PENDING', _('In Attesa')
        PASSED = 'PASSED', _('Esito Positivo')
        FAILED = 'FAILED', _('Esito Negativo')

    application = models.OneToOneField(
        AdoptionApplication,
        on_delete=models.CASCADE,
        related_name='home_visit',
        verbose_name=_('Domanda di Adozione')
    )
    evaluator_name = models.CharField(max_length=150, verbose_name=_('Nome Volontario / Operatore'))
    scheduled_date = models.DateTimeField(verbose_name=_('Data Programmata Visita'))
    completed_date = models.DateTimeField(null=True, blank=True, verbose_name=_('Data Effettiva Esecuzione'))
    outcome = models.CharField(
        max_length=15,
        choices=VisitOutcome.choices,
        default=VisitOutcome.PENDING,
        verbose_name=_('Esito Visita')
    )
    report_notes = models.TextField(blank=True, verbose_name=_('Relazione e Note della Visita'))

    class Meta:
        verbose_name = _('Visita Pre-Affido')
        verbose_name_plural = _('Visite Pre-Affido')

    def __str__(self):
        return f"Visita per {self.application.animal.name} - {self.get_outcome_display()}"