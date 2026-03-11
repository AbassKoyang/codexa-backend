from django.urls import path
from .views import ListCreateProjectView
urlpatterns = [
    path('projects/', ListCreateProjectView.as_view(), name='list-create-project')
]