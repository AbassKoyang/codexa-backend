from django.db import models
from django.conf import settings

User = settings.AUTH_USER_MODEL


# Create your models here.

class PostQuerySet(models.QuerySet):
    def active(self):
        return self.filter(is_deleted=False)

class PostManager(models.Manager):
    def get_queryset(self):
        return PostQuerySet(self.model, using=self._db)

class Project(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='projects')
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    file_tree = models.JSONField(default=dict)
    is_deleted = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = PostManager()

    class Meta:
        ordering = ['-created_at']
        unique_together=("owner", "slug")

    
    def __str__(self):
        return self.name

