from unittest.mock import patch
from uuid import uuid4

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.mock_prep.models import (
    InterviewSession,
    InterviewTrack,
    Question,
    QuestionCategory,
    SessionStatus,
    Technology,
)
from apps.profiles.models import EngineerLevel

User = get_user_model()


class MockPrepAPITestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="candidate@example.com",
            password="StrongPass123!",
        )
        self.other_user = User.objects.create_user(
            email="other@example.com",
            password="StrongPass123!",
        )

        self.track = InterviewTrack.objects.create(
            name="Backend Engineer",
            slug="backend-test",
            is_active=True,
        )
        self.tech_python = Technology.objects.create(
            name="Python",
            slug="python-test",
            is_active=True,
        )
        self.tech_python.tracks.add(self.track)

        self.questions = []
        for index in range(16):
            question = Question.objects.create(
                prompt=f"Test question {index + 1}?",
                category=QuestionCategory.TECHNICAL,
                level=EngineerLevel.MID,
                estimated_minutes=2,
                is_active=True,
            )
            question.tracks.add(self.track)
            question.technologies.add(self.tech_python)
            self.questions.append(question)

        self.tracks_url = reverse("mock-prep-track-list")
        self.technologies_url = reverse("mock-prep-technology-list")
        self.sessions_url = reverse("mock-prep-session-list")

    def test_list_tracks_requires_auth(self):
        response = self.client.get(self.tracks_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_tracks_authenticated(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.tracks_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertGreaterEqual(len(response.data["data"]), 1)

    def test_list_technologies_filtered_by_track(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(
            self.technologies_url,
            {"track": str(self.track.id)},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        tech_ids = [item["id"] for item in response.data["data"]]
        self.assertIn(str(self.tech_python.id), tech_ids)

    def test_create_session(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            self.sessions_url,
            {
                "track_id": str(self.track.id),
                "level": EngineerLevel.MID,
                "technology_ids": [str(self.tech_python.id)],
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data["success"])
        self.assertEqual(response.data["data"]["status"], SessionStatus.SETUP)

    @patch("apps.mock_prep.services.orchestrator.InterviewOrchestratorService._call_structured")
    def test_start_session(self, mock_call_structured):
        selected_ids = [str(question.id) for question in self.questions]
        mock_call_structured.return_value = {
            "question_ids": selected_ids,
            "opening_message": "Welcome! Let's begin with your first question.",
        }

        session = InterviewSession.objects.create(
            user=self.user,
            track=self.track,
            level=EngineerLevel.MID,
            status=SessionStatus.SETUP,
        )
        session.technologies.set([self.tech_python])

        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            reverse("mock-prep-session-start", kwargs={"pk": session.id}),
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        session.refresh_from_db()
        self.assertEqual(session.status, SessionStatus.ACTIVE)
        self.assertEqual(session.session_questions.count(), 16)
        self.assertEqual(session.turns.count(), 1)

    @patch("apps.mock_prep.services.orchestrator.InterviewOrchestratorService._call_structured")
    def test_submit_turn_and_complete(self, mock_call_structured):
        session = InterviewSession.objects.create(
            user=self.user,
            track=self.track,
            level=EngineerLevel.MID,
            status=SessionStatus.ACTIVE,
            target_question_count=1,
            current_question_index=0,
        )
        session.technologies.set([self.tech_python])

        question = self.questions[0]
        from apps.mock_prep.models import SessionQuestion, SessionTurn, TurnRole

        SessionQuestion.objects.create(session=session, question=question, order=1)
        SessionTurn.objects.create(
            session=session,
            role=TurnRole.INTERVIEWER,
            content="Tell me about yourself.",
            question=question,
            order=1,
        )

        mock_call_structured.side_effect = [
            {
                "interviewer_message": "Thank you. That concludes our session.",
                "action": "end_session",
                "next_question_id": None,
                "answer_score": 8,
                "feedback": "Good structured answer.",
            },
            {
                "overall_score": 8,
                "strengths": ["Clear communication"],
                "weaknesses": ["Could add more metrics"],
                "recommendations": ["Practice STAR format"],
                "question_breakdown": [
                    {
                        "question_id": str(question.id),
                        "question_prompt": question.prompt,
                        "score": 8,
                        "feedback": "Solid answer.",
                    }
                ],
            },
        ]

        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            reverse("mock-prep-session-turns", kwargs={"pk": session.id}),
            {"content": "I am a backend engineer with five years of experience."},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["data"]["is_complete"])
        session.refresh_from_db()
        self.assertEqual(session.status, SessionStatus.COMPLETED)
        self.assertIsNotNone(session.summary)

    def test_user_cannot_access_other_users_session(self):
        session = InterviewSession.objects.create(
            user=self.other_user,
            track=self.track,
            level=EngineerLevel.MID,
        )

        self.client.force_authenticate(user=self.user)
        response = self.client.get(
            reverse("mock-prep-session-detail", kwargs={"pk": session.id}),
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class QuestionSelectorTestCase(APITestCase):
    def setUp(self):
        self.track = InterviewTrack.objects.create(
            name="Frontend",
            slug="frontend-selector",
            is_active=True,
        )
        self.tech = Technology.objects.create(
            name="React",
            slug="react-selector",
            is_active=True,
        )
        self.tech.tracks.add(self.track)

        for index in range(16):
            question = Question.objects.create(
                prompt=f"Selector question {index}",
                category=QuestionCategory.BEHAVIORAL,
                level=EngineerLevel.MID,
                is_active=True,
            )
            question.tracks.add(self.track)
            question.technologies.add(self.tech)

    def test_filter_candidate_questions(self):
        from apps.mock_prep.services.question_selector import filter_candidate_questions

        results = filter_candidate_questions(
            self.track,
            EngineerLevel.MID,
            [str(self.tech.id)],
        )
        self.assertGreaterEqual(results.count(), 15)

    def test_validate_selected_question_ids_rejects_invalid(self):
        from apps.mock_prep.services.question_selector import (
            filter_candidate_questions,
            validate_selected_question_ids,
        )

        candidates = filter_candidate_questions(
            self.track,
            EngineerLevel.MID,
            [str(self.tech.id)],
        )

        with self.assertRaises(ValueError):
            validate_selected_question_ids([str(uuid4())], candidates)
