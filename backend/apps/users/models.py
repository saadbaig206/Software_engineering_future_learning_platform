import hashlib
import uuid
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils import timezone


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email).lower()
        extra_fields.setdefault("username", email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", User.Role.ADMIN)
        extra_fields.setdefault("is_email_verified", True)
        extra_fields.setdefault("terms_accepted", True)
        extra_fields.setdefault("privacy_accepted", True)

        if extra_fields.get("is_staff") is not True or extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_staff=True and is_superuser=True")
        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    class Role(models.TextChoices):
        GUEST = "GUEST", "Guest"
        LEARNER = "LEARNER", "Learner"
        INSTRUCTOR = "INSTRUCTOR", "Instructor"
        MODERATOR = "MODERATOR", "Moderator"
        ADMIN = "ADMIN", "Administrator"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = models.CharField(max_length=254, unique=True)
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.LEARNER, db_index=True)

    # Verification & Password Recovery (FR-AUTH-01, FR-AUTH-04)
    is_email_verified = models.BooleanField(default=False)
    email_verification_token = models.CharField(max_length=128, blank=True, null=True, db_index=True)
    email_verification_sent_at = models.DateTimeField(blank=True, null=True)
    password_reset_token = models.CharField(max_length=128, blank=True, null=True, db_index=True)
    password_reset_sent_at = models.DateTimeField(blank=True, null=True)

    # GDPR Consent Capture (FR-AUTH-05)
    terms_accepted = models.BooleanField(default=False)
    privacy_accepted = models.BooleanField(default=False)
    marketing_consent = models.BooleanField(default=False)
    consent_timestamp = models.DateTimeField(blank=True, null=True)
    consent_ip_hash = models.CharField(max_length=64, blank=True, null=True)

    # Profile & Identity
    avatar = models.URLField(max_length=500, blank=True, null=True)
    bio = models.TextField(blank=True, default="")
    preferred_language = models.CharField(max_length=10, default="en")

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        ordering = ["-date_joined"]
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self):
        return f"{self.email} ({self.role})"

    @property
    def is_learner(self):
        return self.role == self.Role.LEARNER

    @property
    def is_instructor(self):
        return self.role in [self.Role.INSTRUCTOR, self.Role.ADMIN]

    @property
    def is_moderator(self):
        return self.role in [self.Role.MODERATOR, self.Role.ADMIN]

    @property
    def is_administrator(self):
        return self.role == self.Role.ADMIN or self.is_superuser

    def has_role(self, role):
        if self.role == self.Role.ADMIN or self.is_superuser:
            return True
        return self.role == role

    def record_consent(self, terms=True, privacy=True, marketing=False, ip_address=None):
        """Records explicit GDPR consent with SHA-256 IP hash and timestamp."""
        self.terms_accepted = bool(terms)
        self.privacy_accepted = bool(privacy)
        self.marketing_consent = bool(marketing)
        self.consent_timestamp = timezone.now()
        if ip_address:
            self.consent_ip_hash = hashlib.sha256(ip_address.encode("utf-8")).hexdigest()
        self.save(update_fields=[
            "terms_accepted", "privacy_accepted", "marketing_consent",
            "consent_timestamp", "consent_ip_hash"
        ])
