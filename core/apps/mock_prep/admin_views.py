from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.common.responses import api_response
from apps.common.viewsets import BaseModelViewSet
from apps.mock_prep.admin_filters import (
    AdminInterviewTrackFilter,
    AdminQuestionFilter,
    AdminTechnologyFilter,
)
from apps.mock_prep.admin_serializers import (
    AdminInterviewTrackSerializer,
    AdminQuestionSerializer,
    AdminTechnologySerializer,
)
from apps.mock_prep.models import InterviewTrack, Question, QuestionCategory, Technology
from apps.mock_prep.permissions import IsStaffUser
from apps.profiles.models import EngineerLevel


class AdminInterviewTrackViewSet(BaseModelViewSet):
    permission_classes = [IsAuthenticated, IsStaffUser]
    queryset = InterviewTrack.objects.all()
    serializer_class = AdminInterviewTrackSerializer
    filterset_class = AdminInterviewTrackFilter
    search_fields = ["name", "slug", "description"]
    ordering_fields = ["name", "created_at", "is_active"]
    ordering = ["name"]


class AdminTechnologyViewSet(BaseModelViewSet):
    permission_classes = [IsAuthenticated, IsStaffUser]
    queryset = Technology.objects.prefetch_related("tracks")
    serializer_class = AdminTechnologySerializer
    filterset_class = AdminTechnologyFilter
    search_fields = ["name", "slug"]
    ordering_fields = ["name", "created_at", "is_active"]
    ordering = ["name"]


class AdminQuestionViewSet(BaseModelViewSet):
    permission_classes = [IsAuthenticated, IsStaffUser]
    queryset = Question.objects.prefetch_related("tracks", "technologies")
    serializer_class = AdminQuestionSerializer
    filterset_class = AdminQuestionFilter
    search_fields = ["prompt"]
    ordering_fields = ["created_at", "level", "category", "estimated_minutes"]
    ordering = ["-created_at"]


class AdminMockPrepMetaView(APIView):
    permission_classes = [IsAuthenticated, IsStaffUser]

    def get(self, request):
        return api_response(
            success=True,
            message="Success",
            data={
                "categories": [
                    {"value": choice.value, "label": choice.label}
                    for choice in QuestionCategory
                ],
                "engineer_levels": [
                    {"value": choice.value, "label": choice.label}
                    for choice in EngineerLevel
                ],
            },
        )
