from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.profiles.views import (
    EducationViewSet,
    ProfileView,
    UserSkillViewSet,
    WorkExperienceViewSet,
)

router = DefaultRouter()
router.register("experiences", WorkExperienceViewSet, basename="profile-experience")
router.register("education", EducationViewSet, basename="profile-education")
router.register("skills", UserSkillViewSet, basename="profile-skill")

urlpatterns = [
    path("", ProfileView.as_view(), name="profile-detail"),
    path("", include(router.urls)),
]
