from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.users.models import User
from apps.core.models import Animal, AdoptionApplication


class MatchResult(models.Model):
    adopter = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='match_results',
        verbose_name=_('Adottante')
    )
    animal = models.ForeignKey(
        Animal,
        on_delete=models.CASCADE,
        related_name='match_results',
        verbose_name=_('Animale')
    )
    overall_score = models.FloatField(verbose_name=_('Punteggio Compatibilità Globale (0-100)'))

    # Scomposizione dettagliata delle feature (Feature Importance)
    score_breakdown = models.JSONField(
        default=dict,
        help_text=_('JSON contenente i dettagli per sottocategoria: lifestyle, space, experience, etc.'),
        verbose_name=_('Scomposizione Punteggio')
    )

    # Output dal modello Cox Survival (`cox_survival_model.joblib`)
    predicted_adoption_time_days = models.FloatField(
        null=True,
        blank=True,
        verbose_name=_('Tempo Stimato di Adozione (Giorni da Cox Model)')
    )
    survival_probability_30d = models.FloatField(
        null=True,
        blank=True,
        verbose_name=_('Probabilità Adozione entro 30gg')
    )

    calculated_at = models.DateTimeField(auto_now=True, verbose_name=_('Data Calcolo'))

    class Meta:
        verbose_name = _('Risultato Matching ML')
        verbose_name_plural = _('Risultati Matching ML')
        unique_together = ('adopter', 'animal')
        indexes = [
            models.Index(fields=['adopter', '-overall_score']),
        ]

    def __str__(self):
        return f"Match {self.adopter.username} <-> {self.animal.name}: {self.overall_score:.1f}%"


class AdoptionFeedback(models.Model):
    application = models.OneToOneField(
        AdoptionApplication,
        on_delete=models.CASCADE,
        related_name='feedback',
        verbose_name=_('Domanda di Adozione')
    )
    adoption_successful = models.BooleanField(default=True, verbose_name=_('Adozione Riuscita con Successo'))
    satisfaction_rating = models.PositiveIntegerField(
        default=5,
        help_text=_('Valutazione da 1 (molto insoddisfatto) a 5 (eccellente)'),
        verbose_name=_('Punteggio Soddisfazione')
    )
    return_reason = models.TextField(blank=True, verbose_name=_('Motivo eventuale rinuncia / restituzione'))
    feedback_notes = models.TextField(blank=True, verbose_name=_('Note dell\'Adottante o del Rifugio'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Data Feedback'))

    class Meta:
        verbose_name = _('Feedback Adozione (ML Retraining Data)')
        verbose_name_plural = _('Feedback Adozioni')

    def __str__(self):
        status = "Riuscita" if self.adoption_successful else "Restituzione"
        return f"Feedback #{self.application.id} - {status}"