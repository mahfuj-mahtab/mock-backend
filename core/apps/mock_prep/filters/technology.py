import django_filters

from apps.mock_prep.models import Technology


class TechnologyFilter(django_filters.FilterSet):
    track = django_filters.UUIDFilter(field_name="tracks__id")

    class Meta:
        model = Technology
        fields = ["track"]
