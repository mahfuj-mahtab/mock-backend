from django.db import models


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
