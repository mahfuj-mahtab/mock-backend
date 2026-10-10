from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from apps.common.serializers import BaseModelSerializer
from apps.profiles.serializers import ProfileSummarySerializer

User = get_user_model()


class UserSerializer(BaseModelSerializer):
    profile = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "date_joined",
            "is_staff",
            "is_superuser",
            "profile",
        ]
        read_only_fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "date_joined",
            "is_staff",
            "is_superuser",
            "profile",
        ]

    def get_profile(self, obj):
        from apps.profiles.services import ProfileService

        profile = ProfileService.get_profile(obj)
        return ProfileSummarySerializer(profile, context=self.context).data


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True, min_length=8)
    first_name = serializers.CharField(required=False, allow_blank=True, max_length=150)
    last_name = serializers.CharField(required=False, allow_blank=True, max_length=150)

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value.lower()

    def validate_password(self, value):
        validate_password(value)
        return value

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError(
                {"password_confirm": ["Passwords do not match."]}
            )
        return attrs


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = User.EMAIL_FIELD

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["email"] = user.email
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data["user"] = UserSerializer(
            self.user,
            context={"request": self.context.get("request")},
        ).data
        return data
