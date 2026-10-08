import json
from typing import Any

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from openai import OpenAI
from rest_framework.exceptions import ValidationError

from apps.mock_prep.models import (
    InterviewSession,
    Question,
    SessionQuestion,
    SessionStatus,
    SessionTurn,
    TurnRole,
)
from apps.mock_prep.prompts.interviewer import (
    SESSION_START_SCHEMA,
    SESSION_SUMMARY_SCHEMA,
    SYSTEM_PROMPT,
    TURN_RESPONSE_SCHEMA,
)
from apps.mock_prep.services.question_selector import (
    filter_candidate_questions,
    serialize_questions_for_ai,
    validate_selected_question_ids,
)


class InterviewOrchestratorService:
    MODEL = "gpt-4o-mini"

    @classmethod
    def _get_client(cls) -> OpenAI:
        api_key = getattr(settings, "OPENAI_API_KEY", "")
        if not api_key:
            raise ValidationError(
                {"detail": ["OpenAI API key is not configured on the server."]}
            )
        return OpenAI(api_key=api_key)

    @classmethod
    def _call_structured(
        cls,
        messages: list[dict[str, str]],
        schema: dict[str, Any],
        schema_name: str,
    ) -> dict[str, Any]:
        client = cls._get_client()
        response = client.chat.completions.create(
            model=cls.MODEL,
            messages=messages,
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": schema_name,
                    "strict": True,
                    "schema": schema,
                },
            },
        )
        content = response.choices[0].message.content or "{}"
        return json.loads(content)

    @classmethod
    def _build_session_context(cls, session: InterviewSession) -> str:
        tech_names = list(session.technologies.values_list("name", flat=True))
        return (
            f"Interview track: {session.track.name}\n"
            f"Candidate level: {session.get_level_display()}\n"
            f"Technologies: {', '.join(tech_names)}\n"
            f"Target questions: {session.target_question_count}\n"
            f"Session duration: {session.duration_minutes} minutes"
        )

    @classmethod
    def _get_next_turn_order(cls, session: InterviewSession) -> int:
        last_turn = session.turns.order_by("-order").first()
        return (last_turn.order + 1) if last_turn else 1

    @classmethod
    @transaction.atomic
    def start_session(cls, session: InterviewSession) -> InterviewSession:
        if session.status != SessionStatus.SETUP:
            raise ValidationError({"detail": ["Session has already been started."]})

        technology_ids = list(session.technologies.values_list("id", flat=True))
        candidates = filter_candidate_questions(
            session.track,
            session.level,
            technology_ids,
        )

        if candidates.count() < 2:
            raise ValidationError(
                {
                    "detail": [
                        "Not enough questions in the bank for this selection. "
                        "Try different technologies or contact an admin."
                    ]
                }
            )

        question_payload = serialize_questions_for_ai(candidates)
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"{cls._build_session_context(session)}\n\n"
                    f"Select between 15 and 20 questions from this bank for the session. "
                    f"Mix behavioral, technical, and system design appropriately.\n\n"
                    f"Question bank:\n{json.dumps(question_payload, indent=2)}\n\n"
                    "Return the ordered question IDs and a warm opening message that "
                    "introduces the interview and asks the first question naturally."
                ),
            },
        ]

        result = cls._call_structured(messages, SESSION_START_SCHEMA, "session_start")
        selected_questions = validate_selected_question_ids(
            result["question_ids"],
            candidates,
        )

        session.status = SessionStatus.ACTIVE
        session.started_at = timezone.now()
        session.current_question_index = 0
        session.save(update_fields=["status", "started_at", "current_question_index"])

        for index, question in enumerate(selected_questions, start=1):
            SessionQuestion.objects.create(
                session=session,
                question=question,
                order=index,
                asked_at=timezone.now() if index == 1 else None,
            )

        first_question = selected_questions[0]
        SessionTurn.objects.create(
            session=session,
            role=TurnRole.INTERVIEWER,
            content=result["opening_message"],
            question=first_question,
            order=1,
            ai_metadata={"type": "opening"},
        )

        session.target_question_count = len(selected_questions)
        session.save(update_fields=["target_question_count"])
        return session

    @classmethod
    def _get_session_questions(cls, session: InterviewSession) -> list[SessionQuestion]:
        return list(
            session.session_questions.select_related("question").order_by("order")
        )

    @classmethod
    def _build_conversation_history(cls, session: InterviewSession) -> str:
        turns = session.turns.select_related("question").order_by("order")
        lines = []
        for turn in turns:
            prefix = "Interviewer" if turn.role == TurnRole.INTERVIEWER else "Candidate"
            lines.append(f"{prefix}: {turn.content}")
        return "\n".join(lines)

    @classmethod
    @transaction.atomic
    def submit_user_turn(
        cls,
        session: InterviewSession,
        content: str,
    ) -> dict[str, Any]:
        if session.status != SessionStatus.ACTIVE:
            raise ValidationError({"detail": ["Session is not active."]})

        content = content.strip()
        if not content:
            raise ValidationError({"content": ["Answer cannot be empty."]})

        session_questions = cls._get_session_questions(session)
        if not session_questions:
            raise ValidationError({"detail": ["Session has no questions configured."]})

        current_index = session.current_question_index
        current_sq = session_questions[current_index]
        turn_order = cls._get_next_turn_order(session)

        SessionTurn.objects.create(
            session=session,
            role=TurnRole.USER,
            content=content,
            question=current_sq.question,
            order=turn_order,
        )

        remaining_questions = session_questions[current_index + 1 :]
        remaining_payload = [
            {
                "id": str(sq.question.id),
                "prompt": sq.question.prompt,
                "category": sq.question.category,
            }
            for sq in remaining_questions
        ]

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"{cls._build_session_context(session)}\n\n"
                    f"Current question (ID: {current_sq.question.id}):\n"
                    f"{current_sq.question.prompt}\n\n"
                    f"Remaining questions in bank:\n"
                    f"{json.dumps(remaining_payload, indent=2)}\n\n"
                    f"Progress: question {current_index + 1} of "
                    f"{len(session_questions)}\n\n"
                    f"Conversation so far:\n{cls._build_conversation_history(session)}\n\n"
                    "Respond as the interviewer. Evaluate the candidate's latest answer. "
                    "Use follow_up for clarification, next_question to advance, or "
                    "end_session if all questions are done."
                ),
            },
        ]

        result = cls._call_structured(messages, TURN_RESPONSE_SCHEMA, "turn_response")

        next_question = current_sq.question
        if result["action"] == "next_question":
            if current_index + 1 >= len(session_questions):
                result["action"] = "end_session"
            else:
                session.current_question_index = current_index + 1
                session.save(update_fields=["current_question_index"])
                next_sq = session_questions[session.current_question_index]
                next_sq.asked_at = timezone.now()
                next_sq.save(update_fields=["asked_at"])
                next_question = next_sq.question

                if result.get("next_question_id"):
                    next_id = str(result["next_question_id"])
                    if next_id != str(next_question.id):
                        raise ValidationError(
                            {"detail": ["AI returned an invalid next question ID."]}
                        )

        elif result["action"] == "end_session":
            if current_index + 1 < len(session_questions):
                session.current_question_index = len(session_questions) - 1
                session.save(update_fields=["current_question_index"])

        SessionTurn.objects.create(
            session=session,
            role=TurnRole.INTERVIEWER,
            content=result["interviewer_message"],
            question=next_question,
            order=turn_order + 1,
            ai_metadata={
                "action": result["action"],
                "answer_score": result.get("answer_score"),
                "feedback": result.get("feedback"),
            },
        )

        is_complete = result["action"] == "end_session"
        if is_complete:
            cls.complete_session(session)

        session.refresh_from_db()
        return {
            "interviewer_message": result["interviewer_message"],
            "action": result["action"],
            "answer_score": result.get("answer_score"),
            "feedback": result.get("feedback"),
            "current_question_index": session.current_question_index,
            "total_questions": len(session_questions),
            "is_complete": is_complete,
        }

    @classmethod
    @transaction.atomic
    def complete_session(cls, session: InterviewSession) -> InterviewSession:
        if session.status == SessionStatus.COMPLETED:
            return session

        session_questions = cls._get_session_questions(session)
        question_summary = [
            {
                "id": str(sq.question.id),
                "prompt": sq.question.prompt,
                "category": sq.question.category,
            }
            for sq in session_questions
        ]

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"{cls._build_session_context(session)}\n\n"
                    f"Questions covered:\n{json.dumps(question_summary, indent=2)}\n\n"
                    f"Full conversation:\n{cls._build_conversation_history(session)}\n\n"
                    "Generate a comprehensive session summary with scores and feedback."
                ),
            },
        ]

        summary = cls._call_structured(
            messages,
            SESSION_SUMMARY_SCHEMA,
            "session_summary",
        )

        session.summary = summary
        session.status = SessionStatus.COMPLETED
        session.ended_at = timezone.now()
        session.save(update_fields=["summary", "status", "ended_at"])
        return session
