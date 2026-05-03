from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
 
# Imports depuis les autres groupes
from apps.users.models import User, CV
from apps.jobs.models import JobOffer
 
 
# ─────────────────────────────────────────────
#  Table : applications
# ─────────────────────────────────────────────
class Application(models.Model):
    """
    Table pivot centrale du système de matching.
    Relie un candidat (User) à une offre (JobOffer) via son CV.
 
    Stocke les scores de compatibilité calculés par le moteur NLP :
      matching_score = 0.5*cosine + 0.25*jaccard + 0.15*exp_match + 0.10*geo_match
 
    La contrainte unique_together garantit qu'un candidat
    ne peut postuler qu'une seule fois par offre.
    """
 
    class Status(models.TextChoices):
        PENDING   = 'pending',   'En attente'
        ACCEPTED  = 'accepted',  'Acceptée'
        REJECTED  = 'rejected',  'Refusée'
        WITHDRAWN = 'withdrawn', 'Retirée'
 
    user          = models.ForeignKey(
                        User,
                        on_delete=models.CASCADE,
                        related_name='applications',
                        db_column='user_id'
                    )
    job           = models.ForeignKey(
                        JobOffer,
                        on_delete=models.CASCADE,
                        related_name='applications',
                        db_column='job_id'
                    )
    cv            = models.ForeignKey(
                        CV,
                        on_delete=models.CASCADE,
                        related_name='applications',
                        db_column='cv_id'
                    )
    status        = models.CharField(
                        max_length=20,
                        choices=Status.choices,
                        default=Status.PENDING
                    )
    cover_letter  = models.TextField(blank=True)
 
    # ── Scores de matching ──────────────────
    matching_score = models.FloatField(null=True, blank=True)
    cosine_score   = models.FloatField(null=True, blank=True)
    jaccard_score  = models.FloatField(null=True, blank=True)
    exp_match      = models.FloatField(null=True, blank=True)
    geo_match      = models.FloatField(null=True, blank=True)
 
    # ── Dates & Review ──────────────────────
    applied_at    = models.DateTimeField(default=timezone.now)
    reviewed_at   = models.DateTimeField(null=True, blank=True)
    reviewed_by   = models.ForeignKey(
                        User,
                        on_delete=models.SET_NULL,
                        null=True,
                        blank=True,
                        related_name='reviewed_applications',
                        db_column='reviewed_by'
                    )
 
    class Meta:
        app_label = 'matching'
        db_table = 'applications'
        unique_together = ('user', 'job')
        verbose_name = 'Candidature'
        verbose_name_plural = 'Candidatures'
        ordering = ['-matching_score', '-applied_at']
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['job']),
            models.Index(fields=['status']),
            models.Index(fields=['-matching_score']),
        ]
 
    def __str__(self):
        return f"{self.user.get_full_name()} → {self.job.title} [{self.status}]"
 
    def compute_score(self):
        """
        Calcule et sauvegarde le score final pondéré.
        Appelé par le moteur data_engine après le calcul NLP.
        """
        scores = [self.cosine_score, self.jaccard_score, self.exp_match, self.geo_match]
        if all(s is not None for s in scores):
            self.matching_score = (
                0.50 * self.cosine_score  +
                0.25 * self.jaccard_score +
                0.15 * self.exp_match     +
                0.10 * self.geo_match
            )
            self.save(update_fields=['matching_score'])
 
    def accept(self, reviewed_by_user):
        """Accepte la candidature — déclenche le signal → notification."""
        self.status      = self.Status.ACCEPTED
        self.reviewed_at = timezone.now()
        self.reviewed_by = reviewed_by_user
        self.save(update_fields=['status', 'reviewed_at', 'reviewed_by'])
 
    def reject(self, reviewed_by_user):
        """Refuse la candidature — déclenche le signal → notification."""
        self.status      = self.Status.REJECTED
        self.reviewed_at = timezone.now()
        self.reviewed_by = reviewed_by_user
        self.save(update_fields=['status', 'reviewed_at', 'reviewed_by'])
 
 
# ─────────────────────────────────────────────
#  Table : notifications
# ─────────────────────────────────────────────
class Notification(models.Model):
    """
    Notification envoyée à un utilisateur.
    Créée automatiquement via le signal post_save sur Application
    lorsqu'une candidature est acceptée ou refusée.
    """
 
    class Type(models.TextChoices):
        ACCEPTED  = 'application_accepted', 'Candidature acceptée'
        REJECTED  = 'application_rejected', 'Candidature refusée'
        NEW_OFFER = 'new_offer',            'Nouvelle offre disponible'
        CLOSED    = 'offer_closed',         'Offre fermée'
        SYSTEM    = 'system',               'Système'
 
    user           = models.ForeignKey(
                         User,
                         on_delete=models.CASCADE,
                         related_name='notifications',
                         db_column='user_id'
                     )
    application    = models.ForeignKey(
                         Application,
                         on_delete=models.SET_NULL,
                         null=True,
                         blank=True,
                         related_name='notifications',
                         db_column='application_id'
                     )
    type           = models.CharField(max_length=50, choices=Type.choices)
    title          = models.CharField(max_length=255)
    message        = models.TextField()
    is_read        = models.BooleanField(default=False)
    created_at     = models.DateTimeField(default=timezone.now)
 
    class Meta:
        app_label = 'matching'
        db_table = 'notifications'
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
        ordering = ['-created_at']
        indexes = [
            # Index partiel : uniquement les non lues → très performant
            models.Index(
                fields=['user', 'is_read'],
                name='idx_notifs_user_unread',
                condition=models.Q(is_read=False)
            ),
        ]
 
    def __str__(self):
        return f"[{self.type}] → {self.user.get_full_name()} ({'lue' if self.is_read else 'non lue'})"
 
    def mark_as_read(self):
        self.is_read = True
        self.save(update_fields=['is_read'])
 
 
# ─────────────────────────────────────────────
#  Table : search_history
# ─────────────────────────────────────────────
class SearchHistory(models.Model):
    """
    Historique des recherches d'offres effectuées par un candidat.
    search_params (JSON) stocke les filtres appliqués :
    location, contract_type, score_min, keywords, etc.
    """
 
    user          = models.ForeignKey(
                        User,
                        on_delete=models.CASCADE,
                        related_name='search_history',
                        db_column='user_id'
                    )
    cv            = models.ForeignKey(
                        CV,
                        on_delete=models.CASCADE,
                        related_name='search_history',
                        db_column='cv_id'
                    )
    search_params = models.JSONField(default=dict, blank=True)
    results_count = models.PositiveIntegerField(default=0)
    searched_at   = models.DateTimeField(default=timezone.now)
 
    class Meta:
        app_label = 'matching'
        db_table = 'search_history'
        verbose_name = 'Historique de recherche'
        verbose_name_plural = 'Historiques de recherches'
        ordering = ['-searched_at']
        indexes = [
            models.Index(fields=['user', '-searched_at']),
        ]
 
    def __str__(self):
        return f"Recherche de {self.user.get_full_name()} le {self.searched_at:%d/%m/%Y %H:%M}"
 
 
# ═══════════════════════════════════════════════════════════════
#  SIGNAL : déclenchement automatique des notifications
#  Équivalent du TRIGGER PostgreSQL — géré côté Django
# ═══════════════════════════════════════════════════════════════
@receiver(post_save, sender=Application)
def auto_notify_on_status_change(sender, instance, created, **kwargs):
    """
    Signal post_save sur Application.
    Crée automatiquement une Notification quand le statut
    passe à 'accepted' ou 'rejected'.
    Ne se déclenche pas à la création (created=True → statut = pending).
    """
    if created:
        return  # Nouvelle candidature — pas encore de décision
 
    if instance.status == Application.Status.ACCEPTED:
        Notification.objects.create(
            user        = instance.user,
            application = instance,
            type        = Notification.Type.ACCEPTED,
            title       = "🎉 Candidature acceptée !",
            message     = (
                f"Félicitations {instance.user.first_name} ! "
                f"Votre candidature pour le poste \"{instance.job.title}\" "
                f"chez {instance.job.company} a été acceptée."
            ),
        )
 
    elif instance.status == Application.Status.REJECTED:
        Notification.objects.create(
            user        = instance.user,
            application = instance,
            type        = Notification.Type.REJECTED,
            title       = "Candidature non retenue",
            message     = (
                f"Bonjour {instance.user.first_name}, "
                f"votre candidature pour le poste \"{instance.job.title}\" "
                f"chez {instance.job.company} n'a pas été retenue."
            ),
        )
 
 