from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import SocialAccount
from apps.accounts.services import AuthService

User = get_user_model()

GITHUB_USER_DATA = {
    "id": 12345,
    "email": "github@example.com",
    "name": "Git Hub",
    "html_url": "https://github.com/githhub",
}


@override_settings(
    GITHUB_CLIENT_ID="test-client-id",
    GITHUB_CLIENT_SECRET="test-client-secret",
    GITHUB_CALLBACK_URL="http://localhost:8000/api/v1/auth/github/callback/",
    FRONTEND_URL="http://localhost:3000",
)
class GitHubOAuthAPITestCase(APITestCase):
    def setUp(self):
        self.start_url = reverse("auth-github-start")
        self.callback_url = reverse("auth-github-callback")

    def test_github_start_redirects_to_github(self):
        response = self.client.get(self.start_url)

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertIn("github.com/login/oauth/authorize", response.url)
        self.assertIn("client_id=test-client-id", response.url)
        self.assertIn("state=", response.url)

    @override_settings(GITHUB_CLIENT_ID="")
    def test_github_start_without_client_id_redirects_to_login_error(self):
        response = self.client.get(self.start_url)

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(response.url, "http://localhost:3000/login?error=github_auth_failed")

    def test_github_callback_rejects_invalid_state(self):
        session = self.client.session
        session["github_oauth_state"] = "expected-state"
        session.save()

        response = self.client.get(
            f"{self.callback_url}?code=test-code&state=wrong-state",
        )

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(response.url, "http://localhost:3000/login?error=github_auth_failed")

    def test_github_callback_rejects_missing_code(self):
        session = self.client.session
        session["github_oauth_state"] = "expected-state"
        session.save()

        response = self.client.get(
            f"{self.callback_url}?state=expected-state",
        )

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(response.url, "http://localhost:3000/login?error=github_auth_failed")

    @patch("apps.accounts.github_oauth.GitHubOAuthCallbackView._fetch_github_user")
    @patch("apps.accounts.github_oauth.GitHubOAuthCallbackView._exchange_code_for_token")
    def test_github_callback_creates_new_user(self, mock_exchange, mock_fetch):
        mock_exchange.return_value = "github-access-token"
        mock_fetch.return_value = GITHUB_USER_DATA

        session = self.client.session
        session["github_oauth_state"] = "expected-state"
        session.save()

        response = self.client.get(
            f"{self.callback_url}?code=test-code&state=expected-state",
        )

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertIn("http://localhost:3000/auth/github/callback?", response.url)
        self.assertIn("access=", response.url)
        self.assertIn("refresh=", response.url)

        user = User.objects.get(email="github@example.com")
        self.assertTrue(
            SocialAccount.objects.filter(
                user=user,
                provider=SocialAccount.PROVIDER_GITHUB,
                provider_user_id="12345",
            ).exists()
        )
        self.assertEqual(user.first_name, "Git")
        self.assertEqual(user.last_name, "Hub")
        self.assertEqual(user.profile.github_url, "https://github.com/githhub")
        self.assertFalse(user.profile.onboarding_completed)

    @patch("apps.accounts.github_oauth.GitHubOAuthCallbackView._fetch_github_user")
    @patch("apps.accounts.github_oauth.GitHubOAuthCallbackView._exchange_code_for_token")
    def test_github_callback_logs_in_existing_social_account(self, mock_exchange, mock_fetch):
        user = User.objects.create_user(
            email="github@example.com",
            password="StrongPass123!",
        )
        SocialAccount.objects.create(
            user=user,
            provider=SocialAccount.PROVIDER_GITHUB,
            provider_user_id="12345",
        )

        mock_exchange.return_value = "github-access-token"
        mock_fetch.return_value = GITHUB_USER_DATA

        session = self.client.session
        session["github_oauth_state"] = "expected-state"
        session.save()

        response = self.client.get(
            f"{self.callback_url}?code=test-code&state=expected-state",
        )

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(User.objects.filter(email="github@example.com").count(), 1)

    @patch("apps.accounts.github_oauth.GitHubOAuthCallbackView._fetch_github_user")
    @patch("apps.accounts.github_oauth.GitHubOAuthCallbackView._exchange_code_for_token")
    def test_github_callback_links_existing_email_user(self, mock_exchange, mock_fetch):
        user = User.objects.create_user(
            email="github@example.com",
            password="StrongPass123!",
        )

        mock_exchange.return_value = "github-access-token"
        mock_fetch.return_value = GITHUB_USER_DATA

        session = self.client.session
        session["github_oauth_state"] = "expected-state"
        session.save()

        response = self.client.get(
            f"{self.callback_url}?code=test-code&state=expected-state",
        )

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertTrue(
            SocialAccount.objects.filter(
                user=user,
                provider=SocialAccount.PROVIDER_GITHUB,
                provider_user_id="12345",
            ).exists()
        )


class GitHubAuthServiceTestCase(APITestCase):
    def test_github_login_or_register_raises_without_email(self):
        with self.assertRaises(Exception):
            AuthService.github_login_or_register({"id": 99999})
