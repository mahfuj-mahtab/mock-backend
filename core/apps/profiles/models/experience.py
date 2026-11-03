from django.conf import settings
from django.db import models

from apps.common.models import BaseModel


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
