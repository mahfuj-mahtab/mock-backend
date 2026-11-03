import random
from collections import defaultdict

from django.db.models import QuerySet

from apps.mock_prep.models import InterviewTrack, Question
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


def select_session_questions(questions: QuerySet[Question], count: int) -> list[Question]:
    pool = list(questions)
    if count <= 0 or not pool:
        return []
    if len(pool) <= count:
        random.shuffle(pool)
        return pool

    by_category: dict[str, list[Question]] = defaultdict(list)
    for question in pool:
        by_category[question.category].append(question)

    for items in by_category.values():
        random.shuffle(items)

    categories = list(by_category.keys())
    random.shuffle(categories)
    selected: list[Question] = []
    while len(selected) < count and any(by_category.values()):
        for category in categories:
            bucket = by_category[category]
            if bucket and len(selected) < count:
                selected.append(bucket.pop())
    return selected


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
