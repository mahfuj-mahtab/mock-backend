import io

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from PIL import Image
from rest_framework import status
from rest_framework.test import APITestCase

from apps.profiles.models import UserProfile, UserSkill, WorkExperience

User = get_user_model()


class ProfileAPITestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="engineer@example.com",
            password="StrongPass123!",
            first_name="Ada",
            last_name="Lovelace",
        )
        self.other_user = User.objects.create_user(
            email="other@example.com",
            password="StrongPass123!",
        )
        self.profile_url = reverse("profile-detail")
        self.experiences_url = reverse("profile-experience-list")
        self.education_url = reverse("profile-education-list")
        self.skills_url = reverse("profile-skill-list")

    def test_profile_auto_created_on_register(self):
        response = self.client.post(
            reverse("auth-register"),
            {
                "email": "new@example.com",
                "password": "StrongPass123!",
                "password_confirm": "StrongPass123!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(email="new@example.com")
        profile = UserProfile.objects.get(user=user)
        self.assertFalse(profile.onboarding_completed)

    def test_get_profile_authenticated(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.get(self.profile_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertEqual(response.data["data"]["email"], self.user.email)
        self.assertIn("experiences", response.data["data"])
        self.assertIn("educations", response.data["data"])
        self.assertIn("skills", response.data["data"])

    def test_patch_profile(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.patch(
            self.profile_url,
            {
                "headline": "Senior Backend Engineer",
                "bio": "Building scalable APIs.",
                "level": "senior",
                "location": "London, UK",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertEqual(response.data["data"]["headline"], "Senior Backend Engineer")
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.level, "senior")

    def test_create_and_list_experience(self):
        self.client.force_authenticate(user=self.user)

        create_response = self.client.post(
            self.experiences_url,
            {
                "company": "Acme Corp",
                "title": "Software Engineer",
                "location": "Remote",
                "start_date": "2022-01-01",
                "is_current": True,
                "description": "Built APIs.",
            },
            format="json",
        )

        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(create_response.data["data"]["company"], "Acme Corp")

        list_response = self.client.get(self.experiences_url)
        self.assertEqual(len(list_response.data["data"]), 1)

    def test_cannot_access_other_users_experience(self):
        experience = WorkExperience.objects.create(
            user=self.other_user,
            company="Other Co",
            title="Engineer",
            start_date="2020-01-01",
        )
        self.client.force_authenticate(user=self.user)

        response = self.client.patch(
            reverse("profile-experience-detail", kwargs={"pk": experience.id}),
            {"title": "Hacked"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_add_skill(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            self.skills_url,
            {"skill_name": "Python", "proficiency": "expert"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["data"]["skill"]["name"], "python")
        self.assertTrue(UserSkill.objects.filter(user=self.user, skill__name="python").exists())

    def test_reject_invalid_cv_file(self):
        self.client.force_authenticate(user=self.user)
        invalid_cv = SimpleUploadedFile("resume.txt", b"not a cv", content_type="text/plain")

        response = self.client.patch(
            self.profile_url,
            {"cv": invalid_cv},
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data["success"])
        self.assertIn("cv", response.data["errors"])

    def test_upload_cv_success(self):
        self.client.force_authenticate(user=self.user)
        valid_cv = SimpleUploadedFile(
            "resume.pdf",
            b"%PDF-1.4 test content",
            content_type="application/pdf",
        )

        response = self.client.patch(
            self.profile_url,
            {"cv": valid_cv},
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["data"]["has_cv"])

    def test_upload_avatar_success(self):
        self.client.force_authenticate(user=self.user)
        image_buffer = io.BytesIO()
        Image.new("RGB", (100, 100), color="red").save(image_buffer, format="JPEG")
        image_buffer.seek(0)
        avatar = SimpleUploadedFile("avatar.jpg", image_buffer.read(), content_type="image/jpeg")

        response = self.client.patch(
            self.profile_url,
            {"avatar": avatar},
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(response.data["data"]["avatar"])

    def test_patch_onboarding_completed_without_other_fields(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.patch(
            self.profile_url,
            {"onboarding_completed": True},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertTrue(response.data["data"]["onboarding_completed"])
        self.user.profile.refresh_from_db()
        self.assertTrue(self.user.profile.onboarding_completed)

    def test_patch_onboarding_completed_persists_in_database(self):
        self.client.force_authenticate(user=self.user)

        self.client.patch(
            self.profile_url,
            {"onboarding_completed": True},
            format="json",
        )

        self.user.profile.refresh_from_db()
        self.assertTrue(self.user.profile.onboarding_completed)

    def test_me_includes_profile_summary(self):
        self.client.force_authenticate(user=self.user)
        self.user.profile.headline = "Backend Engineer"
        self.user.profile.save(update_fields=["headline"])

        response = self.client.get(reverse("auth-me"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("profile", response.data["data"])
        self.assertEqual(response.data["data"]["profile"]["headline"], "Backend Engineer")
