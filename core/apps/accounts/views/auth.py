from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from apps.accounts.serializers import (
    CustomTokenObtainPairSerializer,
    RegisterSerializer,
    UserSerializer,
)
from apps.accounts.services import AuthService
from apps.common.responses import api_response

User = get_user_model()


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        validated_data = serializer.validated_data
        user = AuthService.register_user(
            email=validated_data["email"],
            password=validated_data["password"],
            first_name=validated_data.get("first_name", ""),
            last_name=validated_data.get("last_name", ""),
        )

        refresh = RefreshToken.for_user(user)
        return api_response(
            success=True,
            message="Registration successful",
            data={
                "user": UserSerializer(user, context={"request": request}).data,
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            },
            status=status.HTTP_201_CREATED,
        )


class CustomTokenObtainPairView(TokenObtainPairView):
    permission_classes = [AllowAny]
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code != status.HTTP_200_OK:
            detail = response.data.get("detail", "Authentication failed")
            return api_response(
                success=False,
                message=detail,
                errors=response.data,
                status=response.status_code,
            )

        return api_response(
            success=True,
            message="Login successful",
            data=response.data,
        )


class CustomTokenRefreshView(TokenRefreshView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code != status.HTTP_200_OK:
            detail = response.data.get("detail", "Token refresh failed")
            return api_response(
                success=False,
                message=detail,
                errors=response.data,
                status=response.status_code,
            )

        return api_response(
            success=True,
            message="Token refreshed successfully",
            data=response.data,
        )


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return api_response(
            success=True,
            message="Success",
            data=UserSerializer(request.user, context={"request": request}).data,
        )
