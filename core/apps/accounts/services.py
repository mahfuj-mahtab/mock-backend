import logging

from django.contrib.auth import get_user_model
from django.db import IntegrityError
from rest_framework.exceptions import ValidationError

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
