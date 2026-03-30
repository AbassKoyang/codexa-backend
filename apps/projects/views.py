from rest_framework import generics, permissions
from .models import Project
from .serializers import ProjectSerializer

class ListCreateProjectView(generics.ListCreateAPIView):
    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Project.objects.filter(owner=self.request.user).active()

    def perform_create(self, serializer):
        user = self.request.user
        if user.plan == 'free':
            project_count = Project.objects.filter(owner=user).active().count()
            if project_count >= 3:
                from rest_framework.exceptions import ValidationError
                raise ValidationError("Free users are limited to 3 projects. Please upgrade to a paid plan.")
        serializer.save(owner=user)

class ProjectDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'slug'

    def get_queryset(self):
        return Project.objects.filter(owner=self.request.user).active()

    def perform_destroy(self, instance):
        instance.is_deleted = True
        instance.save()

class DeleteProjectView(generics.DestroyAPIView):
    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'slug'

    def get_queryset(self):
        return Project.objects.filter(owner=self.request.user).active()

    def perform_destroy(self, instance):
        instance.is_deleted = True
        instance.save()
