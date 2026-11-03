from django.db import models


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
