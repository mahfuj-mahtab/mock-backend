from rest_framework import serializers

from apps.common.serializers import BaseModelSerializer, BaseReadSerializer, BaseWriteSerializer
from apps.profiles.models import Education, Skill, UserProfile, UserSkill, WorkExperience
from apps.profiles.services import ProfileService


class ProfileSummarySerializer(BaseReadSerializer):
    avatar = serializers.SerializerMethodField()
    cv = serializers.SerializerMethodField()
    has_cv = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = [
            "headline",
            "bio",
            "level",
            "location",
            "phone",
            "linkedin_url",
            "github_url",
            "portfolio_url",
            "avatar",
            "cv",
            "has_cv",
            "onboarding_completed",
        ]

    def get_avatar(self, obj):
        if obj.avatar:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(obj.avatar.url)
            return obj.avatar.url
        return None

    def get_cv(self, obj):
        if obj.cv:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(obj.cv.url)
            return obj.cv.url
        return None

    def get_has_cv(self, obj) -> bool:
        return bool(obj.cv)


class ProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = [
            "headline",
            "bio",
            "level",
            "location",
            "phone",
            "linkedin_url",
            "github_url",
            "portfolio_url",
            "avatar",
            "cv",
            "onboarding_completed",
        ]
        extra_kwargs = {
            "avatar": {"required": False, "allow_null": True},
            "cv": {"required": False, "allow_null": True},
        }

    def update(self, instance, validated_data):
        return ProfileService.update_profile(self.context["request"].user, validated_data)


class WorkExperienceSerializer(BaseModelSerializer):
    class Meta:
        model = WorkExperience
        fields = [
            "id",
            "company",
            "title",
            "location",
            "start_date",
            "end_date",
            "is_current",
            "description",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate(self, attrs):
        is_current = attrs.get(
            "is_current",
            getattr(self.instance, "is_current", False) if self.instance else False,
        )
        end_date = attrs.get(
            "end_date",
            getattr(self.instance, "end_date", None) if self.instance else None,
        )
        start_date = attrs.get(
            "start_date",
            getattr(self.instance, "start_date", None) if self.instance else None,
        )

        if is_current:
            attrs["end_date"] = None
        elif end_date and start_date and end_date < start_date:
            raise serializers.ValidationError(
                {"end_date": ["End date must be on or after start date."]}
            )

        return attrs

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)


class EducationSerializer(BaseModelSerializer):
    class Meta:
        model = Education
        fields = [
            "id",
            "institution",
            "degree",
            "field_of_study",
            "start_date",
            "end_date",
            "description",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate(self, attrs):
        end_date = attrs.get(
            "end_date",
            getattr(self.instance, "end_date", None) if self.instance else None,
        )
        start_date = attrs.get(
            "start_date",
            getattr(self.instance, "start_date", None) if self.instance else None,
        )

        if end_date and start_date and end_date < start_date:
            raise serializers.ValidationError(
                {"end_date": ["End date must be on or after start date."]}
            )

        return attrs

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)


class SkillSerializer(BaseReadSerializer):
    class Meta:
        model = Skill
        fields = ["id", "name"]


class UserSkillReadSerializer(BaseReadSerializer):
    skill = SkillSerializer(read_only=True)

    class Meta:
        model = UserSkill
        fields = ["id", "skill", "proficiency", "created_at", "updated_at"]


class UserSkillWriteSerializer(BaseWriteSerializer):
    skill_name = serializers.CharField(max_length=100, write_only=True)

    class Meta:
        model = UserSkill
        fields = ["skill_name", "proficiency"]

    def create(self, validated_data):
        skill_name = validated_data.pop("skill_name")
        return ProfileService.add_skill(
            user=self.context["request"].user,
            skill_name=skill_name,
            proficiency=validated_data["proficiency"],
        )

    def update(self, instance, validated_data):
        return ProfileService.update_skill(
            user=self.context["request"].user,
            user_skill=instance,
            validated_data=validated_data,
        )


class ProfileDetailSerializer(serializers.Serializer):
    def _file_url(self, file_field):
        if not file_field:
            return None
        request = self.context.get("request")
        if request:
            return request.build_absolute_uri(file_field.url)
        return file_field.url

    def to_representation(self, instance):
        profile = instance["profile"]
        user = profile.user
        return {
            "id": str(user.id),
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "date_joined": user.date_joined,
            "headline": profile.headline,
            "bio": profile.bio,
            "level": profile.level,
            "location": profile.location,
            "phone": profile.phone,
            "linkedin_url": profile.linkedin_url,
            "github_url": profile.github_url,
            "portfolio_url": profile.portfolio_url,
            "avatar": self._file_url(profile.avatar),
            "cv": self._file_url(profile.cv),
            "has_cv": bool(profile.cv),
            "onboarding_completed": profile.onboarding_completed,
            "experiences": WorkExperienceSerializer(
                instance["experiences"], many=True, context=self.context
            ).data,
            "educations": EducationSerializer(
                instance["educations"], many=True, context=self.context
            ).data,
            "skills": UserSkillReadSerializer(
                instance["skills"], many=True, context=self.context
            ).data,
        }
