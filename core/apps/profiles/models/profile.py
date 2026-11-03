import os
import uuid

from django.conf import settings
from django.db import models

from apps.common.models import BaseModel
from apps.profiles.models.choices import EngineerLevel


def avatar_upload_path(instance, filename: str) -> str:
    extension = os.path.splitext(filename)[1].lower()
    return f"avatars/{instance.user_id}/{uuid.uuid4()}{extension}"


def cv_upload_path(instance, filename: str) -> str:
    extension = os.path.splitext(filename)[1].lower()
    return f"cvs/{instance.user_id}/{uuid.uuid4()}{extension}"


class UserProfile(BaseModel):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    headline = models.CharField(max_length=255, blank=True)
    bio = models.TextField(blank=True)
    level = models.CharField(
        max_length=20,
        choices=EngineerLevel.choices,
        blank=True,
    )
    location = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    linkedin_url = models.URLField(blank=True)
    github_url = models.URLField(blank=True)
    portfolio_url = models.URLField(blank=True)
    avatar = models.ImageField(upload_to=avatar_upload_path, blank=True, null=True)
    cv = models.FileField(upload_to=cv_upload_path, blank=True, null=True)
    onboarding_completed = models.BooleanField(default=False)

    class Meta:
        verbose_name = "User profile"
        verbose_name_plural = "User profiles"

    def __str__(self) -> str:
        return f"Profile for {self.user.email}"
