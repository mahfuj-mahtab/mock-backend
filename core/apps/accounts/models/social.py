from django.db import models

from apps.accounts.models.user import User


class SocialAccount(models.Model):
    PROVIDER_GITHUB = "github"

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="social_accounts",
    )
    provider = models.CharField(max_length=32)
    provider_user_id = models.CharField(max_length=255)

    class Meta:
        unique_together = [("provider", "provider_user_id")]

    def __str__(self):
        return f"{self.provider}:{self.provider_user_id} -> {self.user.email}"
