from rest_framework import serializers


class BaseModelSerializer(serializers.ModelSerializer):
    class Meta:
        abstract = True
        read_only_fields = ["id", "created_at", "updated_at"]


class BaseReadSerializer(BaseModelSerializer):
    class Meta(BaseModelSerializer.Meta):
        abstract = True

    def get_fields(self):
        fields = super().get_fields()
        for field in fields.values():
            field.read_only = True
        return fields


class BaseWriteSerializer(BaseModelSerializer):
    class Meta(BaseModelSerializer.Meta):
        abstract = True

    def get_fields(self):
        fields = super().get_fields()
        for name in ("id", "created_at", "updated_at"):
            fields.pop(name, None)
        return fields
