from django.db import models

from apps.common.models import BaseModel
from apps.mock_prep.models.track import InterviewTrack


class Technology(BaseModel):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    tracks = models.ManyToManyField(
        InterviewTrack,
        related_name="technologies",
        blank=True,
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "technologies"

    def __str__(self) -> str:
        return self.name
