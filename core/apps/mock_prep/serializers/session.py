from django.db import transaction
from rest_framework import serializers

from apps.mock_prep.models import (
    InterviewSession,
    InterviewTrack,
    Question,
    SessionQuestion,
    SessionTurn,
    Technology,
)
from apps.profiles.models import EngineerLevel


class InterviewTrackSerializer(serializers.ModelSerializer):
    class Meta:
        model = InterviewTrack
        fields = ("id", "name", "slug", "description")


class TechnologySerializer(serializers.ModelSerializer):
    class Meta:
        model = Technology
        fields = ("id", "name", "slug")


class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = (
            "id",
            "prompt",
            "category",
            "level",
            "estimated_minutes",
        )


class SessionQuestionSerializer(serializers.ModelSerializer):
    question = QuestionSerializer(read_only=True)

    class Meta:
        model = SessionQuestion
        fields = ("id", "order", "asked_at", "question")


class SessionTurnSerializer(serializers.ModelSerializer):
    class Meta:
        model = SessionTurn
        fields = (
            "id",
            "role",
            "content",
            "question",
            "ai_metadata",
            "order",
            "created_at",
        )


class InterviewSessionListSerializer(serializers.ModelSerializer):
    track = InterviewTrackSerializer(read_only=True)

    class Meta:
        model = InterviewSession
        fields = (
            "id",
            "track",
            "level",
            "status",
            "target_question_count",
            "duration_minutes",
            "started_at",
            "ended_at",
            "created_at",
        )


class InterviewSessionDetailSerializer(serializers.ModelSerializer):
    track = InterviewTrackSerializer(read_only=True)
    technologies = TechnologySerializer(many=True, read_only=True)
    session_questions = SessionQuestionSerializer(many=True, read_only=True)
    turns = SessionTurnSerializer(many=True, read_only=True)

    class Meta:
        model = InterviewSession
        fields = (
            "id",
            "track",
            "technologies",
            "level",
            "status",
            "target_question_count",
            "duration_minutes",
            "current_question_index",
            "started_at",
            "ended_at",
            "summary",
            "session_questions",
            "turns",
            "created_at",
        )


class InterviewSessionCreateSerializer(serializers.Serializer):
    track_id = serializers.UUIDField()
    level = serializers.ChoiceField(choices=EngineerLevel.choices)
    technology_ids = serializers.ListField(
        child=serializers.UUIDField(),
        min_length=1,
    )

    def validate_track_id(self, value):
        try:
            return InterviewTrack.objects.get(id=value, is_active=True)
        except InterviewTrack.DoesNotExist:
            raise serializers.ValidationError("Invalid or inactive interview track.")

    def validate_technology_ids(self, value):
        technologies = Technology.objects.filter(id__in=value, is_active=True)
        if technologies.count() != len(value):
            raise serializers.ValidationError(
                "One or more technologies are invalid or inactive."
            )
        return list(technologies)

    @transaction.atomic
    def create(self, validated_data):
        user = self.context["request"].user
        track = validated_data["track_id"]
        technologies = validated_data["technology_ids"]

        session = InterviewSession.objects.create(
            user=user,
            track=track,
            level=validated_data["level"],
        )
        session.technologies.set(technologies)
        return session


class UserTurnSerializer(serializers.Serializer):
    content = serializers.CharField(min_length=1, max_length=10000)
