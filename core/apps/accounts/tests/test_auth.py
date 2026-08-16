from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()


class AuthAPITestCase(APITestCase):
    def setUp(self):
        self.register_url = reverse("auth-register")
        self.login_url = reverse("auth-login")
        self.me_url = reverse("auth-me")
        self.refresh_url = reverse("auth-refresh")
        self.user_data = {
            "email": "test@example.com",
            "password": "StrongPass123!",
            "password_confirm": "StrongPass123!",
            "first_name": "Test",
            "last_name": "User",
        }

    def test_register_success(self):
        response = self.client.post(self.register_url, self.user_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data["success"])
        self.assertEqual(response.data["data"]["user"]["email"], self.user_data["email"])
        self.assertIn("access", response.data["data"])
        self.assertIn("refresh", response.data["data"])
        self.assertTrue(User.objects.filter(email=self.user_data["email"]).exists())

    def test_register_duplicate_email(self):
        User.objects.create_user(
            email=self.user_data["email"],
            password=self.user_data["password"],
        )

        response = self.client.post(self.register_url, self.user_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data["success"])
        self.assertIn("email", response.data["errors"])

    def test_register_password_mismatch(self):
        payload = {**self.user_data, "password_confirm": "DifferentPass123!"}
        response = self.client.post(self.register_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data["success"])
        self.assertIn("password_confirm", response.data["errors"])

    def test_login_success(self):
        User.objects.create_user(
            email=self.user_data["email"],
            password=self.user_data["password"],
        )

        response = self.client.post(
            self.login_url,
            {
                "email": self.user_data["email"],
                "password": self.user_data["password"],
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertIn("access", response.data["data"])
        self.assertIn("refresh", response.data["data"])
        self.assertEqual(response.data["data"]["user"]["email"], self.user_data["email"])

    def test_login_invalid_credentials(self):
        response = self.client.post(
            self.login_url,
            {"email": "wrong@example.com", "password": "WrongPass123!"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertFalse(response.data["success"])

    def test_me_authenticated(self):
        user = User.objects.create_user(
            email=self.user_data["email"],
            password=self.user_data["password"],
            first_name="Test",
            last_name="User",
        )
        self.client.force_authenticate(user=user)

        response = self.client.get(self.me_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertEqual(response.data["data"]["email"], user.email)
        self.assertEqual(response.data["data"]["first_name"], "Test")

    def test_me_unauthorized(self):
        response = self.client.get(self.me_url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_refresh_token_success(self):
        register_response = self.client.post(self.register_url, self.user_data, format="json")
        refresh_token = register_response.data["data"]["refresh"]

        response = self.client.post(
            self.refresh_url,
            {"refresh": refresh_token},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertIn("access", response.data["data"])
