import os
import uuid

from django.conf import settings
from django.db import models

from apps.common.models import BaseModel


def avatar_upload_path(instance, filename: str) -> str:
    extension = os.path.splitext(filename)[1].lower()
    return f"avatars/{instance.user_id}/{uuid.uuid4()}{extension}"


def cv_upload_path(instance, filename: str) -> str:
    extension = os.path.splitext(filename)[1].lower()
    return f"cvs/{instance.user_id}/{uuid.uuid4()}{extension}"


class EngineerLevel(models.TextChoices):
    INTERN = "intern", "Intern"
    JUNIOR = "junior", "Junior"
    MID = "mid", "Mid-level"
    SENIOR = "senior", "Senior"
    LEAD = "lead", "Lead"
    PRINCIPAL = "principal", "Principal"


class ProficiencyLevel(models.TextChoices):
    BEGINNER = "beginner", "Beginner"
    INTERMEDIATE = "intermediate", "Intermediate"
    ADVANCED = "advanced", "Advanced"
    EXPERT = "expert", "Expert"


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


class WorkExperience(BaseModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="work_experiences",
    )
    company = models.CharField(max_length=255)
    title = models.CharField(max_length=255)
    location = models.CharField(max_length=255, blank=True)
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)
    is_current = models.BooleanField(default=False)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["-start_date", "-created_at"]
        verbose_name = "Work experience"
        verbose_name_plural = "Work experiences"

    def __str__(self) -> str:
        return f"{self.title} at {self.company}"


class Education(BaseModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="educations",
    )
    institution = models.CharField(max_length=255)
    degree = models.CharField(max_length=255)
    field_of_study = models.CharField(max_length=255, blank=True)
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["-start_date", "-created_at"]
        verbose_name = "Education"
        verbose_name_plural = "Educations"

    def __str__(self) -> str:
        return f"{self.degree} at {self.institution}"


class Skill(BaseModel):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class UserSkill(BaseModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="user_skills",
    )
    skill = models.ForeignKey(
        Skill,
        on_delete=models.CASCADE,
        related_name="user_skills",
    )
    proficiency = models.CharField(
        max_length=20,
        choices=ProficiencyLevel.choices,
        default=ProficiencyLevel.INTERMEDIATE,
    )

    class Meta:
        ordering = ["skill__name"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "skill"],
                name="unique_user_skill",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.user.email} - {self.skill.name}"
