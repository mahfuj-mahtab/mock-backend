from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.mock_prep.admin_views import (
    AdminInterviewTrackViewSet,
    AdminMockPrepMetaView,
    AdminQuestionViewSet,
    AdminTechnologyViewSet,
)

router = DefaultRouter()
router.register("tracks", AdminInterviewTrackViewSet, basename="admin-mock-prep-track")
router.register("technologies", AdminTechnologyViewSet, basename="admin-mock-prep-technology")
router.register("questions", AdminQuestionViewSet, basename="admin-mock-prep-question")

urlpatterns = [
    path("meta/", AdminMockPrepMetaView.as_view(), name="admin-mock-prep-meta"),
    path("", include(router.urls)),
]
