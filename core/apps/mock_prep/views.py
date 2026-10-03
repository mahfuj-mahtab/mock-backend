from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated

from apps.common.responses import api_response
from apps.common.viewsets import BaseModelViewSet
from apps.mock_prep.filters import TechnologyFilter
from apps.mock_prep.models import InterviewSession, InterviewTrack, Technology
from apps.mock_prep.serializers import (
    InterviewSessionCreateSerializer,
    InterviewSessionDetailSerializer,
    InterviewSessionListSerializer,
    InterviewTrackSerializer,
    TechnologySerializer,
    UserTurnSerializer,
)
from apps.mock_prep.services.orchestrator import InterviewOrchestratorService


class InterviewTrackViewSet(BaseModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = InterviewTrack.objects.filter(is_active=True)
    serializer_class = InterviewTrackSerializer
    http_method_names = ["get", "head", "options"]


class TechnologyViewSet(BaseModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = Technology.objects.filter(is_active=True)
    serializer_class = TechnologySerializer
    filterset_class = TechnologyFilter
    http_method_names = ["get", "head", "options"]


class InterviewSessionViewSet(BaseModelViewSet):
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "post", "head", "options"]

    def get_queryset(self):
        return (
            InterviewSession.objects.filter(user=self.request.user)
            .select_related("track")
            .prefetch_related("technologies", "session_questions__question", "turns")
        )

    def get_serializer_class(self):
        if self.action == "list":
            return InterviewSessionListSerializer
        if self.action == "create":
            return InterviewSessionCreateSerializer
        return InterviewSessionDetailSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        session = serializer.save()
        read_serializer = InterviewSessionDetailSerializer(session)
        return api_response(
            success=True,
            message="Session created successfully",
            data=read_serializer.data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"])
    def start(self, request, pk=None):
        session = self.get_object()
        InterviewOrchestratorService.start_session(session)
        session.refresh_from_db()
        serializer = InterviewSessionDetailSerializer(session)
        return api_response(
            success=True,
            message="Session started successfully",
            data=serializer.data,
        )

    @action(detail=True, methods=["post"])
    def turns(self, request, pk=None):
        session = self.get_object()
        serializer = UserTurnSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        result = InterviewOrchestratorService.submit_user_turn(
            session,
            serializer.validated_data["content"],
        )
        session.refresh_from_db()
        detail = InterviewSessionDetailSerializer(session).data

        return api_response(
            success=True,
            message="Turn submitted successfully",
            data={
                **result,
                "session": detail,
            },
        )

    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        session = self.get_object()
        InterviewOrchestratorService.complete_session(session)
        session.refresh_from_db()
        serializer = InterviewSessionDetailSerializer(session)
        return api_response(
            success=True,
            message="Session completed successfully",
            data=serializer.data,
        )
