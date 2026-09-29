import logging
import secrets
from urllib.parse import urlencode

import requests
from django.conf import settings
from django.shortcuts import redirect
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.services import AuthService

logger = logging.getLogger(__name__)

GITHUB_AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_USER_URL = "https://api.github.com/user"
GITHUB_EMAILS_URL = "https://api.github.com/user/emails"
GITHUB_SCOPES = "read:user user:email"
SESSION_STATE_KEY = "github_oauth_state"


class GitHubOAuthStartView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        if not settings.GITHUB_CLIENT_ID:
            return redirect(f"{settings.FRONTEND_URL}/login?error=github_auth_failed")

        state = secrets.token_urlsafe(32)
        request.session[SESSION_STATE_KEY] = state

        params = {
            "client_id": settings.GITHUB_CLIENT_ID,
            "redirect_uri": settings.GITHUB_CALLBACK_URL,
            "scope": GITHUB_SCOPES,
            "state": state,
        }
        return redirect(f"{GITHUB_AUTHORIZE_URL}?{urlencode(params)}")


class GitHubOAuthCallbackView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        error_redirect = f"{settings.FRONTEND_URL}/login?error=github_auth_failed"

        stored_state = request.session.pop(SESSION_STATE_KEY, None)
        received_state = request.GET.get("state")
        if not stored_state or stored_state != received_state:
            logger.warning("GitHub OAuth state mismatch")
            return redirect(error_redirect)

        code = request.GET.get("code")
        if not code:
            logger.warning("GitHub OAuth callback missing code")
            return redirect(error_redirect)

        try:
            access_token = self._exchange_code_for_token(code)
            github_user = self._fetch_github_user(access_token)
            user = AuthService.github_login_or_register(github_user)
        except (ValidationError, requests.RequestException, KeyError) as exc:
            logger.exception("GitHub OAuth failed: %s", exc)
            return redirect(error_redirect)

        refresh = RefreshToken.for_user(user)
        params = urlencode({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        })
        return redirect(f"{settings.FRONTEND_URL}/auth/github/callback?{params}")

    def _exchange_code_for_token(self, code: str) -> str:
        response = requests.post(
            GITHUB_TOKEN_URL,
            headers={"Accept": "application/json"},
            data={
                "client_id": settings.GITHUB_CLIENT_ID,
                "client_secret": settings.GITHUB_CLIENT_SECRET,
                "code": code,
                "redirect_uri": settings.GITHUB_CALLBACK_URL,
            },
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
        access_token = data.get("access_token")
        if not access_token:
            raise KeyError("access_token missing from GitHub response")
        return access_token

    def _fetch_github_user(self, access_token: str) -> dict:
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/vnd.github+json",
        }

        user_response = requests.get(GITHUB_USER_URL, headers=headers, timeout=10)
        user_response.raise_for_status()
        user_data = user_response.json()

        if not user_data.get("email"):
            emails_response = requests.get(GITHUB_EMAILS_URL, headers=headers, timeout=10)
            emails_response.raise_for_status()
            emails = emails_response.json()
            primary_email = next(
                (item["email"] for item in emails if item.get("primary") and item.get("verified")),
                None,
            )
            if not primary_email:
                verified_email = next(
                    (item["email"] for item in emails if item.get("verified")),
                    None,
                )
                primary_email = verified_email
            user_data["email"] = primary_email

        return user_data
