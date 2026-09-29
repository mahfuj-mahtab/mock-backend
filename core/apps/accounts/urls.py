from django.urls import path

from apps.accounts.github_oauth import GitHubOAuthCallbackView, GitHubOAuthStartView
from apps.accounts.views import (
    CustomTokenObtainPairView,
    CustomTokenRefreshView,
    MeView,
    RegisterView,
)

urlpatterns = [
    path("register/", RegisterView.as_view(), name="auth-register"),
    path("login/", CustomTokenObtainPairView.as_view(), name="auth-login"),
    path("refresh/", CustomTokenRefreshView.as_view(), name="auth-refresh"),
    path("me/", MeView.as_view(), name="auth-me"),
    path("github/", GitHubOAuthStartView.as_view(), name="auth-github-start"),
    path("github/callback/", GitHubOAuthCallbackView.as_view(), name="auth-github-callback"),
]
