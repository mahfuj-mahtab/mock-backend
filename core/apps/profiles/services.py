import os
from typing import Any

from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework.exceptions import ValidationError

from apps.profiles.models import Education, Skill, UserProfile, UserSkill, WorkExperience

User = get_user_model()

CV_ALLOWED_EXTENSIONS = {".pdf", ".doc", ".docx"}
CV_MAX_SIZE_BYTES = 5 * 1024 * 1024
AVATAR_ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
AVATAR_MAX_SIZE_BYTES = 2 * 1024 * 1024


class ProfileService:
    @staticmethod
    def get_profile(user: User) -> UserProfile:
        profile, _ = UserProfile.objects.get_or_create(user=user)
        return profile

    @staticmethod
    def get_full_profile_data(user: User) -> dict[str, Any]:
        profile = ProfileService.get_profile(user)
        experiences = WorkExperience.objects.filter(user=user)
        educations = Education.objects.filter(user=user)
        skills = UserSkill.objects.filter(user=user).select_related("skill")
        return {
            "profile": profile,
            "experiences": experiences,
            "educations": educations,
            "skills": skills,
        }

    @staticmethod
    def validate_cv_file(uploaded_file) -> None:
        extension = os.path.splitext(uploaded_file.name)[1].lower()
        if extension not in CV_ALLOWED_EXTENSIONS:
            raise ValidationError(
                {"cv": ["CV must be a PDF, DOC, or DOCX file."]}
            )
        if uploaded_file.size > CV_MAX_SIZE_BYTES:
            raise ValidationError({"cv": ["CV file must be 5 MB or smaller."]})

    @staticmethod
    def validate_avatar_file(uploaded_file) -> None:
        extension = os.path.splitext(uploaded_file.name)[1].lower()
        if extension not in AVATAR_ALLOWED_EXTENSIONS:
            raise ValidationError(
                {"avatar": ["Avatar must be a JPG, PNG, or WEBP image."]}
            )
        if uploaded_file.size > AVATAR_MAX_SIZE_BYTES:
            raise ValidationError({"avatar": ["Avatar must be 2 MB or smaller."]})

    @staticmethod
    def _delete_file(file_field) -> None:
        if file_field and file_field.name:
            file_field.delete(save=False)

    @staticmethod
    @transaction.atomic
    def update_profile(user: User, validated_data: dict[str, Any]) -> UserProfile:
        profile = ProfileService.get_profile(user)

        if "cv" in validated_data:
            new_cv = validated_data["cv"]
            if new_cv:
                ProfileService.validate_cv_file(new_cv)
                ProfileService._delete_file(profile.cv)
            profile.cv = new_cv

        if "avatar" in validated_data:
            new_avatar = validated_data["avatar"]
            if new_avatar:
                ProfileService.validate_avatar_file(new_avatar)
                ProfileService._delete_file(profile.avatar)
            profile.avatar = new_avatar

        for field in (
            "headline",
            "bio",
            "level",
            "location",
            "phone",
            "linkedin_url",
            "github_url",
            "portfolio_url",
            "onboarding_completed",
        ):
            if field in validated_data:
                setattr(profile, field, validated_data[field])

        profile.save()
        return profile

    @staticmethod
    @transaction.atomic
    def add_skill(user: User, skill_name: str, proficiency: str) -> UserSkill:
        normalized_name = skill_name.strip().lower()
        if not normalized_name:
            raise ValidationError({"skill_name": ["Skill name is required."]})

        skill, _ = Skill.objects.get_or_create(name=normalized_name)

        if UserSkill.objects.filter(user=user, skill=skill).exists():
            raise ValidationError({"skill_name": ["This skill is already on your profile."]})

        return UserSkill.objects.create(
            user=user,
            skill=skill,
            proficiency=proficiency,
        )

    @staticmethod
    def update_skill(user: User, user_skill: UserSkill, validated_data: dict[str, Any]) -> UserSkill:
        if user_skill.user_id != user.id:
            raise ValidationError({"detail": ["You do not have permission to update this skill."]})

        if "proficiency" in validated_data:
            user_skill.proficiency = validated_data["proficiency"]
            user_skill.save(update_fields=["proficiency", "updated_at"])

        return user_skill
