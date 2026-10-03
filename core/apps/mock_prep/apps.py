from django.apps import AppConfig


class MockPrepConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.mock_prep"
    verbose_name = "Mock Prep"
