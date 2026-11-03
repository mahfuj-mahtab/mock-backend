from django.conf import settings
from django.db import models

from apps.common.models import BaseModel
from apps.mock_prep.models.choices import SessionStatus, TurnRole
from apps.mock_prep.models.question import Question
from apps.mock_prep.models.technology import Technology
from apps.mock_prep.models.track import InterviewTrack
from apps.profiles.models import EngineerLevel


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
    target_question_count = models.PositiveSmallIntegerField(default=5)
    duration_minutes = models.PositiveSmallIntegerField(default=15)
    max_followups = models.PositiveSmallIntegerField(default=5)
    max_followups_per_question = models.PositiveSmallIntegerField(default=1)
    current_question_index = models.PositiveSmallIntegerField(default=0)
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    summary = models.JSONField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "started_at"], name="interview_user_started_idx"),
        ]

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
