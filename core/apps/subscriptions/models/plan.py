from django.db import models

from apps.common.models import BaseModel


class SubscriptionPlan(BaseModel):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    is_default = models.BooleanField(default=False)
    monthly_session_limit = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Mocks per month. Blank means unlimited.",
    )
    duration_minutes = models.PositiveSmallIntegerField(default=15)
    question_count = models.PositiveSmallIntegerField(default=5)
    max_followups = models.PositiveSmallIntegerField(default=5)
    max_followups_per_question = models.PositiveSmallIntegerField(default=1)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.is_default:
            SubscriptionPlan.objects.filter(is_default=True).exclude(pk=self.pk).update(
                is_default=False
            )
