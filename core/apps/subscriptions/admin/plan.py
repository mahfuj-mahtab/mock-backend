from django.contrib import admin

from apps.subscriptions.models import SubscriptionPlan


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "slug",
        "monthly_session_limit",
        "duration_minutes",
        "question_count",
        "max_followups",
        "max_followups_per_question",
        "is_default",
    )
    list_editable = (
        "monthly_session_limit",
        "duration_minutes",
        "question_count",
        "max_followups",
        "max_followups_per_question",
    )
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
