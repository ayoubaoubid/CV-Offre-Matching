from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone
 
 
# ─────────────────────────────────────────────
#  Manager personnalisé pour User
# ─────────────────────────────────────────────
class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("L'adresse email est obligatoire.")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
 
    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('role', User.Role.ADMIN)
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)
 
 
# ─────────────────────────────────────────────
#  Table : users
# ─────────────────────────────────────────────
class User(AbstractBaseUser, PermissionsMixin):
    """
    Table centrale unifiée — représente à la fois les admins (recruteurs)
    et les candidats grâce au champ `role`.
    """
 
    class Role(models.TextChoices):
        ADMIN     = 'admin',     'Admin (Recruteur)'
        CANDIDATE = 'candidate', 'Candidat'
 
    email       = models.EmailField(max_length=255, unique=True)
    first_name  = models.CharField(max_length=100)
    last_name   = models.CharField(max_length=100)
    role        = models.CharField(max_length=10, choices=Role.choices, default=Role.CANDIDATE)
    is_active   = models.BooleanField(default=True)
    is_staff    = models.BooleanField(default=False)   # accès admin Django
    created_at  = models.DateTimeField(default=timezone.now)
    updated_at  = models.DateTimeField(auto_now=True)
 
    objects = UserManager()
 
    USERNAME_FIELD  = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']
 
    class Meta:
        app_label = 'users'
        db_table = 'users'
        verbose_name = 'Utilisateur'
        verbose_name_plural = 'Utilisateurs'
 
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.role})"
 
    @property
    def is_admin(self):
        return self.role == self.Role.ADMIN
 
    @property
    def is_candidate(self):
        return self.role == self.Role.CANDIDATE
 
 
# ─────────────────────────────────────────────
#  Table : profiles
# ─────────────────────────────────────────────
class Profile(models.Model):
    """
    Profil étendu — uniquement pour les candidats (1:1 avec User).
    Contient les informations visibles sur la page publique du candidat.
    """
 
    user             = models.OneToOneField(
                           User,
                           on_delete=models.CASCADE,
                           related_name='profile',
                           db_column='user_id'
                       )
    title            = models.CharField(max_length=150, blank=True)
    bio              = models.TextField(blank=True)
    location         = models.CharField(max_length=150, blank=True)
    experience_years = models.PositiveIntegerField(default=0)
    education_level  = models.CharField(max_length=100, blank=True)
    phone            = models.CharField(max_length=20, blank=True)
    linkedin_url     = models.URLField(max_length=300, blank=True)
    avatar_url       = models.URLField(max_length=500, blank=True)
 
    class Meta:
        app_label = 'users'
        db_table = 'profiles'
        verbose_name = 'Profil'
        verbose_name_plural = 'Profils'
 
    def __str__(self):
        return f"Profil de {self.user.get_full_name()}"
 
 
# ─────────────────────────────────────────────
#  Table : cvs
# ─────────────────────────────────────────────
class CV(models.Model):
    """
    CV uploadé par un candidat.
    Plusieurs CVs possibles par utilisateur, un seul actif à la fois (is_active).
    Le champ tfidf_vector stocke le vecteur calculé par le moteur NLP (JSON).
    """
 
    class FileType(models.TextChoices):
        PDF  = 'pdf',  'PDF'
        DOCX = 'docx', 'DOCX'
 
    user         = models.ForeignKey(
                       User,
                       on_delete=models.CASCADE,
                       related_name='cvs',
                       db_column='user_id'
                   )
    file_path    = models.CharField(max_length=500)
    file_type    = models.CharField(max_length=10, choices=FileType.choices)
    raw_text     = models.TextField(blank=True)
    tfidf_vector = models.JSONField(null=True, blank=True)
    is_active    = models.BooleanField(default=True)
    uploaded_at  = models.DateTimeField(default=timezone.now)
 
    class Meta:
        app_label = 'users'
        db_table = 'cvs'
        verbose_name = 'CV'
        verbose_name_plural = 'CVs'
 
    def __str__(self):
        return f"CV de {self.user.get_full_name()} — {self.file_type} ({'actif' if self.is_active else 'archivé'})"
 
    def save(self, *args, **kwargs):
        # Si ce CV est marqué actif, désactiver les autres CVs du même user
        if self.is_active:
            CV.objects.filter(user=self.user, is_active=True).exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)
 
 
# ─────────────────────────────────────────────
#  Table : skills  (référentiel partagé)
# ─────────────────────────────────────────────
class Skill(models.Model):
    """
    Référentiel centralisé des compétences.
    Partagé entre user_skills et job_skills pour éviter la redondance.
    """
 
    class SkillType(models.TextChoices):
        HARD = 'hard', 'Hard Skill'
        SOFT = 'soft', 'Soft Skill'
 
    name     = models.CharField(max_length=150, unique=True)
    type     = models.CharField(max_length=10, choices=SkillType.choices, blank=True)
    category = models.CharField(max_length=100, blank=True)
 
    class Meta:
        app_label = 'users'
        db_table = 'skills'
        verbose_name = 'Compétence'
        verbose_name_plural = 'Compétences'
 
    def __str__(self):
        return f"{self.name} ({self.type})"
 
 
# ─────────────────────────────────────────────
#  Table : user_skills  (liaison N:N)
# ─────────────────────────────────────────────
class UserSkill(models.Model):
    """
    Liaison N:N entre User et Skill.
    Ajoute le niveau de maîtrise du candidat pour chaque compétence.
    """
 
    class Level(models.TextChoices):
        BEGINNER     = 'débutant',      'Débutant'
        INTERMEDIATE = 'intermédiaire', 'Intermédiaire'
        ADVANCED     = 'avancé',        'Avancé'
        EXPERT       = 'expert',        'Expert'
 
    user  = models.ForeignKey(
                User,
                on_delete=models.CASCADE,
                related_name='user_skills',
                db_column='user_id'
            )
    skill = models.ForeignKey(
                Skill,
                on_delete=models.CASCADE,
                related_name='user_skills',
                db_column='skill_id'
            )
    level = models.CharField(max_length=20, choices=Level.choices, blank=True)
 
    class Meta:
        app_label = 'users'
        db_table = 'user_skills'
        unique_together = ('user', 'skill')
        verbose_name = 'Compétence utilisateur'
        verbose_name_plural = 'Compétences utilisateurs'
 
    def __str__(self):
        return f"{self.user.get_full_name()} — {self.skill.name} ({self.level})"