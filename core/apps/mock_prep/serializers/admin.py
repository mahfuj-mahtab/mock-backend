from django.db import transaction
from django.utils.text import slugify
from rest_framework import serializers

from apps.mock_prep.models import InterviewTrack, Question, Technology


def _normalize_slug(value: str) -> str:
    slug = slugify(value, allow_unicode=False)
    return slug[:100] if slug else "item"


def _unique_slug(model, base: str, exclude_pk=None) -> str:
    slug = _normalize_slug(base)
    candidate = slug
    counter = 1
    while True:
        qs = model.objects.filter(slug=candidate)
        if exclude_pk is not None:
            qs = qs.exclude(pk=exclude_pk)
        if not qs.exists():
            return candidate
        counter += 1
        suffix = f"-{counter}"
        candidate = f"{slug[: 100 - len(suffix)]}{suffix}"


class AdminTrackBriefSerializer(serializers.ModelSerializer):
    class Meta:
        model = InterviewTrack
        fields = ("id", "name", "slug", "is_active")


class AdminTechnologyBriefSerializer(serializers.ModelSerializer):
    class Meta:
        model = Technology
        fields = ("id", "name", "slug", "is_active")


class AdminInterviewTrackSerializer(serializers.ModelSerializer):
    class Meta:
        model = InterviewTrack
        fields = (
            "id",
            "name",
            "slug",
            "description",
            "is_active",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")
        extra_kwargs = {
            "slug": {"required": False, "allow_blank": True},
        }

    def validate_slug(self, value):
        if not value:
            return value
        qs = InterviewTrack.objects.filter(slug=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("A track with this slug already exists.")
        return value

    def _resolve_slug(self, validated_data):
        slug = validated_data.get("slug") or ""
        if slug:
            validated_data["slug"] = _normalize_slug(slug)
            return
        name = validated_data.get("name") or (self.instance.name if self.instance else "")
        exclude = self.instance.pk if self.instance else None
        validated_data["slug"] = _unique_slug(InterviewTrack, name, exclude_pk=exclude)

    def create(self, validated_data):
        self._resolve_slug(validated_data)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        if "slug" not in validated_data and "name" in validated_data:
            self._resolve_slug(validated_data)
        elif validated_data.get("slug"):
            validated_data["slug"] = _normalize_slug(validated_data["slug"])
        return super().update(instance, validated_data)


class AdminTechnologySerializer(serializers.ModelSerializer):
    tracks = AdminTrackBriefSerializer(many=True, read_only=True)
    track_ids = serializers.PrimaryKeyRelatedField(
        queryset=InterviewTrack.objects.all(),
        many=True,
        write_only=True,
        required=False,
    )

    class Meta:
        model = Technology
        fields = (
            "id",
            "name",
            "slug",
            "is_active",
            "tracks",
            "track_ids",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "tracks", "created_at", "updated_at")
        extra_kwargs = {
            "slug": {"required": False, "allow_blank": True},
        }

    def validate_slug(self, value):
        if not value:
            return value
        qs = Technology.objects.filter(slug=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("A technology with this slug already exists.")
        return value

    def _resolve_slug(self, validated_data):
        slug = validated_data.get("slug") or ""
        if slug:
            validated_data["slug"] = _normalize_slug(slug)
            return
        name = validated_data.get("name") or (self.instance.name if self.instance else "")
        exclude = self.instance.pk if self.instance else None
        validated_data["slug"] = _unique_slug(Technology, name, exclude_pk=exclude)

    @transaction.atomic
    def create(self, validated_data):
        track_ids = validated_data.pop("track_ids", [])
        self._resolve_slug(validated_data)
        technology = super().create(validated_data)
        if track_ids:
            technology.tracks.set(track_ids)
        return technology

    @transaction.atomic
    def update(self, instance, validated_data):
        track_ids = validated_data.pop("track_ids", None)
        if "slug" not in validated_data and "name" in validated_data:
            self._resolve_slug(validated_data)
        elif validated_data.get("slug"):
            validated_data["slug"] = _normalize_slug(validated_data["slug"])
        technology = super().update(instance, validated_data)
        if track_ids is not None:
            technology.tracks.set(track_ids)
        return technology


class AdminQuestionSerializer(serializers.ModelSerializer):
    tracks = AdminTrackBriefSerializer(many=True, read_only=True)
    technologies = AdminTechnologyBriefSerializer(many=True, read_only=True)
    track_ids = serializers.PrimaryKeyRelatedField(
        queryset=InterviewTrack.objects.all(),
        many=True,
        write_only=True,
    )
    technology_ids = serializers.PrimaryKeyRelatedField(
        queryset=Technology.objects.all(),
        many=True,
        write_only=True,
        required=False,
    )

    class Meta:
        model = Question
        fields = (
            "id",
            "prompt",
            "category",
            "level",
            "estimated_minutes",
            "is_active",
            "tracks",
            "technologies",
            "track_ids",
            "technology_ids",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "tracks", "technologies", "created_at", "updated_at")

    @transaction.atomic
    def create(self, validated_data):
        track_ids = validated_data.pop("track_ids")
        technology_ids = validated_data.pop("technology_ids", [])
        question = super().create(validated_data)
        question.tracks.set(track_ids)
        if technology_ids:
            question.technologies.set(technology_ids)
        return question

    @transaction.atomic
    def update(self, instance, validated_data):
        track_ids = validated_data.pop("track_ids", None)
        technology_ids = validated_data.pop("technology_ids", None)
        question = super().update(instance, validated_data)
        if track_ids is not None:
            question.tracks.set(track_ids)
        if technology_ids is not None:
            question.technologies.set(technology_ids)
        return question
