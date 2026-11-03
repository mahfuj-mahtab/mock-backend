import json
import logging
from datetime import timedelta
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
from apps.mock_prep.prompts.interviewer import SYSTEM_PROMPT, TURN_RESPONSE_SCHEMA
from apps.mock_prep.services.question_selector import (
    filter_candidate_questions,
    select_session_questions,
)
logger = logging.getLogger(__name__)

ANSWER_PROMPT_MAX_CHARS = 800
MAX_COMPLETION_TOKENS = 250

TIME_UP_MESSAGE = "That's the end of our time. I'll put together your summary now."
SESSION_END_MESSAGE = "That's the last question. I'll put your summary together."


class InterviewOrchestratorService:
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
            model=getattr(settings, "OPENAI_MODEL", "gpt-5.4-nano"),
            messages=messages,
            max_completion_tokens=MAX_COMPLETION_TOKENS,
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
    def _get_next_turn_order(cls, session: InterviewSession) -> int:
        last_turn = session.turns.order_by("-order").first()
        return (last_turn.order + 1) if last_turn else 1

    @classmethod
    def _opening_message(cls, session: InterviewSession, first_question: Question) -> str:
        return (
            f"Hi, I'll be your interviewer for this {session.track.name} mock. "
            f"We'll cover {session.target_question_count} questions in "
            f"{session.duration_minutes} minutes. Let's start. {first_question.prompt}"
        )

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

        selected_questions = select_session_questions(
            candidates,
            session.target_question_count,
        )
        session.status = SessionStatus.ACTIVE
        session.started_at = timezone.now()
        session.current_question_index = 0
        session.target_question_count = len(selected_questions)
        session.save(
            update_fields=[
                "status",
                "started_at",
                "current_question_index",
                "duration_minutes",
                "target_question_count",
            ]
        )

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
            content=cls._opening_message(session, first_question),
            question=first_question,
            order=1,
            ai_metadata={"type": "opening"},
        )
        logger.info("Started mock session %s with %s questions", session.pk, len(selected_questions))
        return session

    @classmethod
    def _get_session_questions(cls, session: InterviewSession) -> list[SessionQuestion]:
        return list(
            session.session_questions.select_related("question").order_by("order")
        )

    @classmethod
    def _is_time_up(cls, session: InterviewSession) -> bool:
        if session.started_at is None:
            return False
        deadline = session.started_at + timedelta(minutes=session.duration_minutes)
        return timezone.now() >= deadline

    @classmethod
    def _followup_counts(
        cls,
        session: InterviewSession,
        question_id: Any,
    ) -> tuple[int, int]:
        on_question = 0
        total = 0
        rows = session.turns.filter(role=TurnRole.INTERVIEWER).values_list(
            "question_id",
            "ai_metadata",
        )
        for stored_question_id, metadata in rows:
            if (metadata or {}).get("action") != "follow_up":
                continue
            total += 1
            if stored_question_id == question_id:
                on_question += 1
        return on_question, total

    @classmethod
    def _clamp_action(
        cls,
        action: str,
        *,
        current_index: int,
        total_questions: int,
        followups_on_question: int,
        followups_total: int,
        max_followups: int,
        max_followups_per_question: int,
    ) -> str:
        on_last_question = current_index + 1 >= total_questions
        if action == "follow_up" and (
            followups_on_question >= max_followups_per_question
            or followups_total >= max_followups
        ):
            action = "end_session" if on_last_question else "next_question"
        if action == "next_question" and on_last_question:
            action = "end_session"
        return action

    @classmethod
    def _spoken_message(
        cls,
        result: dict[str, Any],
        action: str,
        next_question: Question | None,
    ) -> str:
        original = result.get("action")
        model_message = (result.get("interviewer_message") or "").strip()
        if action == "follow_up":
            return model_message
        if action == "end_session":
            if original == "end_session" and model_message:
                return model_message
            return SESSION_END_MESSAGE
        if next_question is None:
            return model_message or SESSION_END_MESSAGE
        if original == "next_question" and model_message:
            if next_question.prompt in model_message:
                return model_message
            return f"{model_message}\n\n{next_question.prompt}"
        return f"Thanks for that. Next question: {next_question.prompt}"

    @classmethod
    def _close_for_time(cls, session: InterviewSession, turn_order: int, question: Question) -> dict[str, Any]:
        SessionTurn.objects.create(
            session=session,
            role=TurnRole.INTERVIEWER,
            content=TIME_UP_MESSAGE,
            question=question,
            order=turn_order,
            ai_metadata={"action": "end_session", "reason": "time_up"},
        )
        cls.complete_session(session)
        session.refresh_from_db()
        total_questions = session.session_questions.count()
        return {
            "interviewer_message": TIME_UP_MESSAGE,
            "action": "end_session",
            "answer_score": None,
            "feedback": None,
            "current_question_index": session.current_question_index,
            "total_questions": total_questions,
            "is_complete": True,
        }

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
        if current_index >= len(session_questions):
            current_index = len(session_questions) - 1
        current_sq = session_questions[current_index]
        turn_order = cls._get_next_turn_order(session)

        SessionTurn.objects.create(
            session=session,
            role=TurnRole.USER,
            content=content,
            question=current_sq.question,
            order=turn_order,
        )

        if cls._is_time_up(session):
            return cls._close_for_time(session, turn_order + 1, current_sq.question)

        followups_on_question, followups_total = cls._followup_counts(
            session,
            current_sq.question_id,
        )
        clipped_answer = content[:ANSWER_PROMPT_MAX_CHARS]
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Question {current_index + 1} of {len(session_questions)}. "
                    f"Session length: {session.duration_minutes} minutes.\n"
                    f"Follow-ups already used on this question: {followups_on_question} "
                    f"of {session.max_followups_per_question}.\n"
                    f"Follow-ups used in this session: {followups_total} "
                    f"of {session.max_followups}.\n\n"
                    f"Current question:\n{current_sq.question.prompt}\n\n"
                    f"Candidate answer:\n{clipped_answer}"
                ),
            },
        ]
        result = cls._call_structured(messages, TURN_RESPONSE_SCHEMA, "turn_response")
        action = cls._clamp_action(
            result["action"],
            current_index=current_index,
            total_questions=len(session_questions),
            followups_on_question=followups_on_question,
            followups_total=followups_total,
            max_followups=session.max_followups,
            max_followups_per_question=session.max_followups_per_question,
        )

        next_question = current_sq.question
        if action == "next_question":
            session.current_question_index = current_index + 1
            session.save(update_fields=["current_question_index"])
            next_sq = session_questions[session.current_question_index]
            next_sq.asked_at = timezone.now()
            next_sq.save(update_fields=["asked_at"])
            next_question = next_sq.question

        spoken = cls._spoken_message(result, action, next_question if action != "end_session" else None)
        SessionTurn.objects.create(
            session=session,
            role=TurnRole.INTERVIEWER,
            content=spoken,
            question=next_question,
            order=turn_order + 1,
            ai_metadata={
                "action": action,
                "answer_score": result.get("answer_score"),
                "feedback": result.get("feedback"),
            },
        )

        is_complete = action == "end_session"
        if is_complete:
            cls.complete_session(session)

        session.refresh_from_db()
        return {
            "interviewer_message": spoken,
            "action": action,
            "answer_score": result.get("answer_score"),
            "feedback": result.get("feedback"),
            "current_question_index": session.current_question_index,
            "total_questions": len(session_questions),
            "is_complete": is_complete,
        }

    @classmethod
    def _build_local_summary(cls, session: InterviewSession) -> dict[str, Any]:
        scored_turns = (
            session.turns.filter(role=TurnRole.INTERVIEWER)
            .select_related("question")
            .order_by("order")
        )
        grouped: dict[str, dict[str, Any]] = {}
        for turn in scored_turns:
            metadata = turn.ai_metadata or {}
            score = metadata.get("answer_score")
            if score is None or turn.question_id is None:
                continue
            key = str(turn.question_id)
            bucket = grouped.setdefault(
                key,
                {
                    "prompt": turn.question.prompt if turn.question else "",
                    "scores": [],
                    "feedback": [],
                },
            )
            bucket["scores"].append(float(score))
            feedback = metadata.get("feedback")
            if feedback:
                bucket["feedback"].append(feedback)

        breakdown = []
        strengths: list[str] = []
        weaknesses: list[str] = []
        averages: list[float] = []
        for question_id, bucket in grouped.items():
            average = sum(bucket["scores"]) / len(bucket["scores"])
            averages.append(average)
            feedback = bucket["feedback"][-1] if bucket["feedback"] else ""
            rounded = round(average, 1)
            breakdown.append(
                {
                    "question_id": question_id,
                    "question_prompt": bucket["prompt"],
                    "score": rounded,
                    "feedback": feedback,
                }
            )
            if feedback and rounded >= 7:
                strengths.append(feedback)
            elif feedback:
                weaknesses.append(feedback)

        overall = round(sum(averages) / len(averages), 1) if averages else 0
        return {
            "overall_score": overall,
            "strengths": strengths[:5],
            "weaknesses": weaknesses[:5],
            "recommendations": weaknesses[:3]
            or ["Practice answering with one concrete example."],
            "question_breakdown": breakdown,
        }

    @classmethod
    @transaction.atomic
    def complete_session(cls, session: InterviewSession) -> InterviewSession:
        if session.status == SessionStatus.COMPLETED:
            return session

        session.summary = cls._build_local_summary(session)
        session.status = SessionStatus.COMPLETED
        session.ended_at = timezone.now()
        session.save(update_fields=["summary", "status", "ended_at"])
        return session
