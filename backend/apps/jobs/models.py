from django.db import models
from django.utils import timezone
 
# Import depuis le groupe Users
from apps.users.models import User, Skill
 
 
# ─────────────────────────────────────────────
#  Table : clusters
# ─────────────────────────────────────────────
class Cluster(models.Model):
    """
    Groupe K-means des offres similaires.
    Calculé par le moteur data_engine (scikit-learn).
    Un Cluster regroupe plusieurs JobOffers (1:N).
    """
 
    label      = models.CharField(max_length=150, blank=True)
    k_value    = models.PositiveIntegerField()
    domain     = models.CharField(max_length=150, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
 
    class Meta:
        app_label = 'jobs'
        db_table = 'clusters'
        verbose_name = 'Cluster'
        verbose_name_plural = 'Clusters'
 
    def __str__(self):
        return f"Cluster {self.id} — {self.label or self.domain} (k={self.k_value})"
 
 
# ─────────────────────────────────────────────
#  Table : job_offers
# ─────────────────────────────────────────────
class JobOffer(models.Model):
    """
    Offre d'emploi publiée par un admin (recruteur).
    Liée à un cluster K-means pour le matching groupé.
    Le champ tfidf_vector stocke la représentation vectorielle
    calculée par le moteur NLP pour le scoring de similarité.
    """
 
    class ContractType(models.TextChoices):
        CDI       = 'CDI',       'CDI'
        CDD       = 'CDD',       'CDD'
        STAGE     = 'Stage',     'Stage'
        FREELANCE = 'Freelance', 'Freelance'
 
    class Status(models.TextChoices):
        OPEN   = 'open',   'Ouverte'
        CLOSED = 'closed', 'Fermée'
        DRAFT  = 'draft',  'Brouillon'
 
    admin                = models.ForeignKey(
                               User,
                               on_delete=models.CASCADE,
                               related_name='job_offers',
                               db_column='admin_id',
                               limit_choices_to={'role': 'admin'}
                           )
    cluster              = models.ForeignKey(
                               Cluster,
                               on_delete=models.SET_NULL,
                               null=True,
                               blank=True,
                               related_name='job_offers',
                               db_column='cluster_id'
                           )
    title                = models.CharField(max_length=255)
    description          = models.TextField()
    company              = models.CharField(max_length=255)
    sector               = models.CharField(max_length=150, blank=True)
    location             = models.CharField(max_length=150, blank=True)
    contract_type        = models.CharField(
                               max_length=20,
                               choices=ContractType.choices,
                               blank=True
                           )
    experience_required  = models.PositiveIntegerField(default=0)
    tfidf_vector         = models.JSONField(null=True, blank=True)
    status               = models.CharField(
                               max_length=20,
                               choices=Status.choices,
                               default=Status.OPEN
                           )
    published_at         = models.DateTimeField(null=True, blank=True)
    expires_at           = models.DateField(null=True, blank=True)
    created_at           = models.DateTimeField(default=timezone.now)
 
    class Meta:
        app_label = 'jobs'
        db_table = 'job_offers'
        verbose_name = "Offre d'emploi"
        verbose_name_plural = "Offres d'emploi"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['location']),
            models.Index(fields=['contract_type']),
            models.Index(fields=['admin']),
            models.Index(fields=['cluster']),
        ]
 
    def __str__(self):
        return f"{self.title} — {self.company} ({self.status})"
 
    def publish(self):
        """Publie l'offre et enregistre la date de publication."""
        self.status = self.Status.OPEN
        self.published_at = timezone.now()
        self.save(update_fields=['status', 'published_at'])
 
    def close(self):
        """Ferme l'offre."""
        self.status = self.Status.CLOSED
        self.save(update_fields=['status'])
 
 
# ─────────────────────────────────────────────
#  Table : job_skills  (liaison N:N)
# ─────────────────────────────────────────────
class JobSkill(models.Model):
    """
    Liaison N:N entre JobOffer et Skill.
    Distingue les compétences obligatoires (is_required=True)
    des compétences souhaitées (is_required=False).
    """
 
    job       = models.ForeignKey(
                    JobOffer,
                    on_delete=models.CASCADE,
                    related_name='job_skills',
                    db_column='job_id'
                )
    skill     = models.ForeignKey(
                    Skill,
                    on_delete=models.CASCADE,
                    related_name='job_skills',
                    db_column='skill_id'
                )
    is_required = models.BooleanField(default=True)
 
    class Meta:
        app_label = 'jobs'
        db_table = 'job_skills'
        unique_together = ('job', 'skill')
        verbose_name = "Compétence de l'offre"
        verbose_name_plural = "Compétences des offres"
 
    def __str__(self):
        req = 'requise' if self.is_required else 'souhaitée'
        return f"{self.job.title} — {self.skill.name} ({req})"