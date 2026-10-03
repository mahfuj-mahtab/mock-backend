from django.conf import settings
from django.db import models

from apps.common.models import BaseModel
from apps.profiles.models import EngineerLevel


class QuestionCategory(models.TextChoices):
    BEHAVIORAL = "behavioral", "Behavioral"
    TECHNICAL = "technical", "Technical"
    SYSTEM_DESIGN = "system_design", "System Design"


class SessionStatus(models.TextChoices):
    SETUP = "setup", "Setup"
    ACTIVE = "active", "Active"
    COMPLETED = "completed", "Completed"
    ABANDONED = "abandoned", "Abandoned"


class TurnRole(models.TextChoices):
    INTERVIEWER = "interviewer", "Interviewer"
    USER = "user", "User"


class InterviewTrack(BaseModel):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


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


class InterviewSession(BaseModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="interview_sessions",
    )
    track = models.ForeignKey(
        InterviewTrack,
        on_delete=models.PROTECT,
        related_name="sessions",
    )
    level = models.CharField(max_length=20, choices=EngineerLevel.choices)
    technologies = models.ManyToManyField(Technology, related_name="sessions")
    status = models.CharField(
        max_length=20,
        choices=SessionStatus.choices,
        default=SessionStatus.SETUP,
    )
    target_question_count = models.PositiveSmallIntegerField(default=18)
    duration_minutes = models.PositiveSmallIntegerField(default=40)
    current_question_index = models.PositiveSmallIntegerField(default=0)
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    summary = models.JSONField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.user.email} — {self.track.name} ({self.status})"


class SessionQuestion(BaseModel):
    session = models.ForeignKey(
        InterviewSession,
        on_delete=models.CASCADE,
        related_name="session_questions",
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.PROTECT,
        related_name="session_questions",
    )
    order = models.PositiveSmallIntegerField()
    asked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["order"]
        constraints = [
            models.UniqueConstraint(
                fields=["session", "order"],
                name="unique_session_question_order",
            ),
        ]

    def __str__(self) -> str:
        return f"Session {self.session_id} Q{self.order}"


class SessionTurn(BaseModel):
    session = models.ForeignKey(
        InterviewSession,
        on_delete=models.CASCADE,
        related_name="turns",
    )
    role = models.CharField(max_length=20, choices=TurnRole.choices)
    content = models.TextField()
    question = models.ForeignKey(
        Question,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="turns",
    )
    ai_metadata = models.JSONField(default=dict, blank=True)
    order = models.PositiveSmallIntegerField()

    class Meta:
        ordering = ["order"]
        constraints = [
            models.UniqueConstraint(
                fields=["session", "order"],
                name="unique_session_turn_order",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.role} turn #{self.order}"
