from django.urls import path
from . import views
urlpatterns = [
    path('', views.ListCreateProjectView.as_view(), name='project-list-create'),
    path('<slug:slug>/', views.ProjectDetailView.as_view(), name='project-detail'),
]