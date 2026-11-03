from django.conf import settings
from django.db import models

from apps.common.models import BaseModel


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
