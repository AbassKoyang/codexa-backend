from rest_framework import serializers
from .models import Project
from apps.accounts.serializers import UserSerializer


class ProjectSerializer(serializers.ModelSerializer):
    owner = UserSerializer(read_only=True)

    class Meta:
        model = Project
        fields = [
            "id",
            "owner",
            "name",
            "slug",
            "thumbnail",
            "language",
            "file_tree",
            "is_deleted",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["slug", "created_at", "updated_at"]