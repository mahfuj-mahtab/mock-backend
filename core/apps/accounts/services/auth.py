import logging
from typing import Any

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from rest_framework.exceptions import ValidationError

from apps.accounts.models import SocialAccount

logger = logging.getLogger(__name__)
User = get_user_model()


class AuthService:
    @staticmethod
    def register_user(email, password, **extra_fields):
        try:
            user = User.objects.create_user(
                email=email,
                password=password,
                **extra_fields,
            )
        except IntegrityError:
            raise ValidationError({"email": ["A user with this email already exists."]})

        logger.info("User registered", extra={"user_id": str(user.id), "email": user.email})
        return user

    @staticmethod
    @transaction.atomic
    def github_login_or_register(github_data: dict[str, Any]) -> User:
        github_id = str(github_data["id"])
        email = github_data.get("email")
        if not email:
            raise ValidationError({"email": ["GitHub did not provide a verified email address."]})

        social_account = SocialAccount.objects.filter(
            provider=SocialAccount.PROVIDER_GITHUB,
            provider_user_id=github_id,
        ).select_related("user").first()
        if social_account:
            return social_account.user

        existing_user = User.objects.filter(email__iexact=email).first()
        if existing_user:
            SocialAccount.objects.create(
                user=existing_user,
                provider=SocialAccount.PROVIDER_GITHUB,
                provider_user_id=github_id,
            )
            logger.info(
                "Linked GitHub account to existing user",
                extra={"user_id": str(existing_user.id), "github_id": github_id},
            )
            return existing_user

        name = (github_data.get("name") or "").strip()
        name_parts = name.split(" ", 1) if name else ["", ""]
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ""

        user = User(
            email=email,
            first_name=first_name,
            last_name=last_name,
        )
        user.set_unusable_password()
        user.save()

        SocialAccount.objects.create(
            user=user,
            provider=SocialAccount.PROVIDER_GITHUB,
            provider_user_id=github_id,
        )

        profile = user.profile
        github_url = github_data.get("html_url", "")
        if github_url and not profile.github_url:
            profile.github_url = github_url
            profile.save(update_fields=["github_url"])

        logger.info(
            "User registered via GitHub",
            extra={"user_id": str(user.id), "email": user.email, "github_id": github_id},
        )
        return user
