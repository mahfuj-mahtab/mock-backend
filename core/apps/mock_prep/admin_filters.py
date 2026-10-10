import django_filters

from apps.mock_prep.models import InterviewTrack, Question, Technology


class AdminInterviewTrackFilter(django_filters.FilterSet):
    is_active = django_filters.BooleanFilter()

    class Meta:
        model = InterviewTrack
        fields = ["is_active"]


class AdminTechnologyFilter(django_filters.FilterSet):
    track = django_filters.UUIDFilter(field_name="tracks__id")
    is_active = django_filters.BooleanFilter()

    class Meta:
        model = Technology
        fields = ["track", "is_active"]


class AdminQuestionFilter(django_filters.FilterSet):
    category = django_filters.CharFilter()
    level = django_filters.CharFilter()
    track = django_filters.UUIDFilter(field_name="tracks__id")
    technology = django_filters.UUIDFilter(field_name="technologies__id")
    is_active = django_filters.BooleanFilter()

    class Meta:
        model = Question
        fields = ["category", "level", "track", "technology", "is_active"]
