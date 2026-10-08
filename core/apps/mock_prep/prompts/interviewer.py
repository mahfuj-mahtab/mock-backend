SESSION_START_SCHEMA = {
    "type": "object",
    "properties": {
        "question_ids": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 15,
            "maxItems": 20,
        },
        "opening_message": {"type": "string"},
    },
    "required": ["question_ids", "opening_message"],
    "additionalProperties": False,
}

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

SESSION_SUMMARY_SCHEMA = {
    "type": "object",
    "properties": {
        "overall_score": {"type": "number"},
        "strengths": {
            "type": "array",
            "items": {"type": "string"},
        },
        "weaknesses": {
            "type": "array",
            "items": {"type": "string"},
        },
        "recommendations": {
            "type": "array",
            "items": {"type": "string"},
        },
        "question_breakdown": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "question_id": {"type": "string"},
                    "question_prompt": {"type": "string"},
                    "score": {"type": "number"},
                    "feedback": {"type": "string"},
                },
                "required": ["question_id", "question_prompt", "score", "feedback"],
                "additionalProperties": False,
            },
        },
    },
    "required": [
        "overall_score",
        "strengths",
        "weaknesses",
        "recommendations",
        "question_breakdown",
    ],
    "additionalProperties": False,
}

SYSTEM_PROMPT = """You are a professional mock technical interviewer conducting a verbal interview.

CRITICAL RULES:
1. You may ONLY ask questions from the provided question bank by their IDs.
2. Do NOT invent new interview questions. Follow-ups and clarifications on the current question are allowed.
3. Keep responses concise and natural, as if speaking aloud.
4. Be encouraging but honest in your evaluations.
5. Move to the next question when the candidate has adequately answered or after one brief follow-up.
6. Target pacing for a 40-minute session with 15-20 questions — keep follow-ups short."""
