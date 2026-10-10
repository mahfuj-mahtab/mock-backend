from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.mock_prep.models import InterviewTrack, Question, QuestionCategory, Technology
from apps.profiles.models import EngineerLevel

User = get_user_model()


class AdminMockPrepAPITestCase(APITestCase):
    def setUp(self):
        self.staff = User.objects.create_user(
            email="staff@example.com",
            password="StrongPass123!",
            is_staff=True,
        )
        self.user = User.objects.create_user(
            email="user@example.com",
            password="StrongPass123!",
        )
        self.track = InterviewTrack.objects.create(
            name="Backend",
            slug="backend-admin-test",
            is_active=True,
        )
        self.tech = Technology.objects.create(name="Python", slug="python-admin-test", is_active=True)
        self.tech.tracks.add(self.track)

    def test_non_staff_forbidden_on_tracks_list(self):
        self.client.force_authenticate(user=self.user)
        url = reverse("admin-mock-prep-track-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_staff_can_list_and_create_question(self):
        self.client.force_authenticate(user=self.staff)
        list_url = reverse("admin-mock-prep-question-list")
        response = self.client.get(list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])

        create_url = reverse("admin-mock-prep-question-list")
        payload = {
            "prompt": "Explain Django ORM optimization?",
            "category": QuestionCategory.TECHNICAL,
            "level": EngineerLevel.MID,
            "track_ids": [str(self.track.id)],
            "technology_ids": [str(self.tech.id)],
            "estimated_minutes": 3,
        }
        response = self.client.post(create_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        question_id = response.data["data"]["id"]

        patch_url = reverse("admin-mock-prep-question-detail", kwargs={"pk": question_id})
        response = self.client.patch(patch_url, {"is_active": False}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["data"]["is_active"])

    def test_staff_search_questions(self):
        Question.objects.create(
            prompt="Unique searchable admin prompt",
            category=QuestionCategory.BEHAVIORAL,
            level=EngineerLevel.JUNIOR,
            is_active=True,
        )
        question = Question.objects.get(prompt="Unique searchable admin prompt")
        question.tracks.add(self.track)

        self.client.force_authenticate(user=self.staff)
        url = reverse("admin-mock-prep-question-list")
        response = self.client.get(url, {"search": "searchable admin"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(response.data["pagination"]["count"], 1)

    def test_staff_meta_endpoint(self):
        self.client.force_authenticate(user=self.staff)
        url = reverse("admin-mock-prep-meta")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("categories", response.data["data"])
        self.assertIn("engineer_levels", response.data["data"])

    def test_staff_crud_track(self):
        self.client.force_authenticate(user=self.staff)
        url = reverse("admin-mock-prep-track-list")
        response = self.client.post(
            url,
            {"name": "New Track", "description": "Desc"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        track_id = response.data["data"]["id"]

        detail_url = reverse("admin-mock-prep-track-detail", kwargs={"pk": track_id})
        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
