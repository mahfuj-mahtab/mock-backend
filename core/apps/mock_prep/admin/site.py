from django.contrib import admin

from apps.mock_prep.models import (
    InterviewSession,
    InterviewTrack,
    Question,
    SessionQuestion,
    SessionTurn,
    Technology,
)


@admin.register(InterviewTrack)
class InterviewTrackAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Technology)
class TechnologyAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_active", "created_at")
    list_filter = ("is_active", "tracks")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    filter_horizontal = ("tracks",)


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = (
        "prompt_short",
        "category",
        "level",
        "estimated_minutes",
        "is_active",
    )
    list_filter = ("category", "level", "is_active", "tracks", "technologies")
    search_fields = ("prompt",)
    filter_horizontal = ("tracks", "technologies")

    @admin.display(description="Prompt")
    def prompt_short(self, obj: Question) -> str:
        return obj.prompt[:80]


class SessionQuestionInline(admin.TabularInline):
    model = SessionQuestion
    extra = 0
    readonly_fields = ("question", "order", "asked_at")
    can_delete = False


class SessionTurnInline(admin.TabularInline):
    model = SessionTurn
    extra = 0
    readonly_fields = ("role", "content", "question", "order", "ai_metadata")
    can_delete = False


@admin.register(InterviewSession)
class InterviewSessionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "track",
        "level",
        "status",
        "started_at",
        "ended_at",
    )
    list_filter = ("status", "track", "level")
    search_fields = ("user__email",)
    readonly_fields = (
        "user",
        "track",
        "level",
        "status",
        "target_question_count",
        "duration_minutes",
        "current_question_index",
        "started_at",
        "ended_at",
        "summary",
    )
    inlines = [SessionQuestionInline, SessionTurnInline]
    filter_horizontal = ("technologies",)
