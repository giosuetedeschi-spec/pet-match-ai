from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.users.models import User


class ConsentType(models.TextChoices):
    TERMS = 'TERMS', _('Termini e Condizioni')
    PRIVACY = 'PRIVACY', _('Informativa Privacy GDPR')
    MARKETING = 'MARKETING', _('Comunicazioni Marketing')
    PROFILING = 'PROFILING', _('Profilazione e Algoritmi ML')


class GDPRConsentLog(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='gdpr_consent_logs',
        verbose_name=_('Utente')
    )
    consent_type = models.CharField(
        max_length=20,
        choices=ConsentType.choices,
        verbose_name=_('Tipologia Consenso')
    )
    granted = models.BooleanField(verbose_name=_('Consenso Accordato'))
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name=_('Indirizzo IP (Anonimizzato)'))
    user_agent = models.TextField(blank=True, verbose_name=_('User Agent Browser'))
    privacy_policy_version = models.CharField(max_length=20, default='1.0', verbose_name=_('Versione Informativa'))
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name=_('Data e Ora Registrazione'))

    class Meta:
        verbose_name = _('Registro Consenso GDPR')
        verbose_name_plural = _('Registro Consensi GDPR')
        ordering = ['-timestamp']

    def __str__(self):
        action = "CONCESSO" if self.granted else "REVOCATO"
        return f"{self.user.username} - {self.get_consent_type_display()} [{action}] il {self.timestamp.strftime('%Y-%m-%d %H:%M')}"