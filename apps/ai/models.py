from django.db import models
from apps.projects.models import Project

class ChatMessage(models.Model):
    ROLE_CHOICES = [
        ('user', 'User'),
        ('agent', 'Agent'),
    ]
    
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='chat_messages')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"{self.role} - {self.project.name} - {self.timestamp}"
