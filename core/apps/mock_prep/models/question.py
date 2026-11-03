from django.db import models

from apps.common.models import BaseModel
from apps.mock_prep.models.choices import QuestionCategory
from apps.mock_prep.models.technology import Technology
from apps.mock_prep.models.track import InterviewTrack
from apps.profiles.models import EngineerLevel


class Question(BaseModel):
    prompt = models.TextField()
    category = models.CharField(max_length=20, choices=QuestionCategory.choices)
    level = models.CharField(max_length=20, choices=EngineerLevel.choices)
    tracks = models.ManyToManyField(InterviewTrack, related_name="questions")
    technologies = models.ManyToManyField(Technology, related_name="questions")
    estimated_minutes = models.PositiveSmallIntegerField(default=2)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["category", "level", "created_at"]

    def __str__(self) -> str:
        return f"{self.get_category_display()} ({self.level}): {self.prompt[:60]}"
