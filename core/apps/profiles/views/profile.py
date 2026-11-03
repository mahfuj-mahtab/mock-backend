from rest_framework import status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.common.responses import api_response
from apps.common.viewsets import BaseModelViewSet
from apps.profiles.models import Education, UserSkill, WorkExperience
from apps.profiles.serializers import (
    EducationSerializer,
    ProfileDetailSerializer,
    ProfileSummarySerializer,
    ProfileUpdateSerializer,
    UserSkillReadSerializer,
    UserSkillWriteSerializer,
    WorkExperienceSerializer,
)
from apps.profiles.services import ProfileService


class ProfileView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get(self, request):
        profile_data = ProfileService.get_full_profile_data(request.user)
        serializer = ProfileDetailSerializer(profile_data, context={"request": request})
        return api_response(
            success=True,
            message="Success",
            data=serializer.data,
        )

    def patch(self, request):
        profile = ProfileService.get_profile(request.user)
        serializer = ProfileUpdateSerializer(
            profile,
            data=request.data,
            partial=True,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        updated_profile = serializer.save()
        summary = ProfileSummarySerializer(updated_profile, context={"request": request})
        return api_response(
            success=True,
            message="Profile updated successfully",
            data=summary.data,
        )


class WorkExperienceViewSet(BaseModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = WorkExperienceSerializer

    def get_queryset(self):
        return WorkExperience.objects.filter(user=self.request.user)


class EducationViewSet(BaseModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = EducationSerializer

    def get_queryset(self):
        return Education.objects.filter(user=self.request.user)


class UserSkillViewSet(BaseModelViewSet):
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_queryset(self):
        return UserSkill.objects.filter(user=self.request.user).select_related("skill")

    def get_serializer_class(self):
        if self.action in ("create", "partial_update", "update"):
            return UserSkillWriteSerializer
        return UserSkillReadSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user_skill = serializer.save()
        read_serializer = UserSkillReadSerializer(user_skill, context={"request": request})
        return api_response(
            success=True,
            message="Created successfully",
            data=read_serializer.data,
            status=status.HTTP_201_CREATED,
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        user_skill = serializer.save()
        read_serializer = UserSkillReadSerializer(user_skill, context={"request": request})
        return api_response(
            success=True,
            message="Updated successfully",
            data=read_serializer.data,
        )

    def partial_update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return self.update(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = UserSkillReadSerializer(instance, context={"request": request})
        return api_response(
            success=True,
            message="Success",
            data=serializer.data,
        )

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = UserSkillReadSerializer(queryset, many=True, context={"request": request})
        return api_response(
            success=True,
            message="Success",
            data=serializer.data,
        )
