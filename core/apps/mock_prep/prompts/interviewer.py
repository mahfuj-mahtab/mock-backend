TURN_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "interviewer_message": {"type": "string"},
        "action": {
            "type": "string",
            "enum": ["follow_up", "next_question", "end_session"],
        },
        "next_question_id": {"type": ["string", "null"]},
        "answer_score": {"type": ["number", "null"]},
        "feedback": {"type": ["string", "null"]},
    },
    "required": [
        "interviewer_message",
        "action",
        "next_question_id",
        "answer_score",
        "feedback",
    ],
    "additionalProperties": False,
}

SYSTEM_PROMPT = """You are a professional mock technical interviewer speaking aloud.

Rules:
1. Clarify only the current question. Do not invent a new main question.
2. Reply in one or two short sentences.
3. Free sessions are 15 minutes with 5 main questions. Use follow_up only when the answer is thin. Otherwise use next_question.
4. At most one brief follow-up on the current question, and never more follow-ups than the budget in the prompt.
5. Use end_session only when the last question is finished.
6. Score the latest answer from 1 to 10 and add one short feedback line.
"""
