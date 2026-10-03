from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.mock_prep.views import (
    InterviewSessionViewSet,
    InterviewTrackViewSet,
    TechnologyViewSet,
)

router = DefaultRouter()
router.register("tracks", InterviewTrackViewSet, basename="mock-prep-track")
router.register("technologies", TechnologyViewSet, basename="mock-prep-technology")
router.register("sessions", InterviewSessionViewSet, basename="mock-prep-session")

urlpatterns = [
    path("", include(router.urls)),
]
