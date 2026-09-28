from django.contrib import admin

from apps.profiles.models import Education, Skill, UserProfile, UserSkill, WorkExperience


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "headline", "level", "location", "updated_at")
    search_fields = ("user__email", "headline", "location")
    raw_id_fields = ("user",)


@admin.register(WorkExperience)
class WorkExperienceAdmin(admin.ModelAdmin):
    list_display = ("user", "title", "company", "start_date", "is_current")
    search_fields = ("user__email", "company", "title")
    raw_id_fields = ("user",)


@admin.register(Education)
class EducationAdmin(admin.ModelAdmin):
    list_display = ("user", "degree", "institution", "start_date")
    search_fields = ("user__email", "institution", "degree")
    raw_id_fields = ("user",)


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ("name", "created_at")
    search_fields = ("name",)


@admin.register(UserSkill)
class UserSkillAdmin(admin.ModelAdmin):
    list_display = ("user", "skill", "proficiency")
    search_fields = ("user__email", "skill__name")
    raw_id_fields = ("user", "skill")
