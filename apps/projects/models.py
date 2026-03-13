from django.db import models
from django.conf import settings
from django.utils.text import slugify

User = settings.AUTH_USER_MODEL


# Create your models here.

LANGUAGE_CHOICES = [
    ('python', 'Python'),
    ('javascript', 'JavaScript'),
    ('typescript', 'TypeScript'),
    ('html', 'HTML'),
    ('css', 'CSS'),
    ('react', 'React'),
    ('vue', 'Vue'),
    ('angular', 'Angular'),
    ('svelte', 'Svelte'),
    ('nextjs', 'Next.js'),
    ('django', 'Django'),
    ('flask', 'Flask'),
    ('fastapi', 'FastAPI'),
    ('node', 'Node.js'),
    ('express', 'Express'),
    ('php', 'PHP'),
    ('laravel', 'Laravel'),
    ('ruby', 'Ruby'),
    ('rails', 'Ruby on Rails'),
    ('go', 'Go'),
    ('rust', 'Rust'),
    ('java', 'Java'),
    ('spring', 'Spring Boot'),
    ('c', 'C'),
    ('cpp', 'C++'),
    ('csharp', 'C#'),
    ('dot-net', '.NET'),
    ('swift', 'Swift'),
    ('kotlin', 'Kotlin'),
    ('dart', 'Dart'),
    ('flutter', 'Flutter'),
    ('react-native', 'React Native'),
    ('sql', 'SQL'),
    ('shell', 'Shell/Bash'),
    ('unity', 'Unity'),
    ('unreal', 'Unreal Engine'),
]

class PostQuerySet(models.QuerySet):
    def active(self):
        return self.filter(is_deleted=False)

class PostManager(models.Manager):
    def get_queryset(self):
        return PostQuerySet(self.model, using=self._db)

class Project(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='projects')
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=250)
    thumbnail = models.URLField(blank=True, null=True)
    language = models.CharField(max_length=100, choices=LANGUAGE_CHOICES, default='javascript')
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

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

