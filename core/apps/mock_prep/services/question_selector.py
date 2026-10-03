from typing import Any

from django.db.models import QuerySet

from apps.mock_prep.models import InterviewTrack, Question, Technology
from apps.profiles.models import EngineerLevel


LEVEL_ORDER = [
    EngineerLevel.INTERN,
    EngineerLevel.JUNIOR,
    EngineerLevel.MID,
    EngineerLevel.SENIOR,
    EngineerLevel.LEAD,
    EngineerLevel.PRINCIPAL,
]

MIN_QUESTION_POOL = 15


def _adjacent_levels(level: str) -> list[str]:
    try:
        index = LEVEL_ORDER.index(level)
    except ValueError:
        return [level]

    start = max(0, index - 1)
    end = min(len(LEVEL_ORDER), index + 2)
    return [choice.value for choice in LEVEL_ORDER[start:end]]


def filter_candidate_questions(
    track: InterviewTrack,
    level: str,
    technology_ids: list[str],
) -> QuerySet[Question]:
    base_qs = (
        Question.objects.filter(
            is_active=True,
            tracks=track,
            technologies__id__in=technology_ids,
        )
        .distinct()
        .prefetch_related("tracks", "technologies")
    )

    exact_match = base_qs.filter(level=level)
    if exact_match.count() >= MIN_QUESTION_POOL:
        return exact_match

    widened = base_qs.filter(level__in=_adjacent_levels(level))
    if widened.count() >= MIN_QUESTION_POOL:
        return widened

    return base_qs


def serialize_questions_for_ai(questions: QuerySet[Question]) -> list[dict[str, Any]]:
    return [
        {
            "id": str(question.id),
            "category": question.category,
            "level": question.level,
            "prompt": question.prompt,
            "estimated_minutes": question.estimated_minutes,
        }
        for question in questions
    ]


def validate_selected_question_ids(
    selected_ids: list[str],
    allowed_questions: QuerySet[Question],
) -> list[Question]:
    allowed_map = {str(question.id): question for question in allowed_questions}
    validated: list[Question] = []

    for question_id in selected_ids:
        question = allowed_map.get(str(question_id))
        if question is None:
            raise ValueError(f"Invalid question ID selected: {question_id}")
        validated.append(question)

    return validated
