from django.shortcuts import render
from rest_framework import generics

from .models import Project
from .serializers import ProjectSerializer
# Create your views here.

class ListCreateProjectView(generics.ListCreateAPIView):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer

    def perform_create(self, serializer):
        print(serializer.validated_data)
        serializer.save(owner=self.request.user)

