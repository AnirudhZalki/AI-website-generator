# website_generator/models.py
from django.db import models
from django.contrib.auth.models import User
import uuid


class Project(models.Model):
    PROJECT_TYPES = [
        ('static', 'Static Website'),
        ('fullstack', 'Full-Stack Website'),
    ]

    STACK_CHOICES = [
        ('html_css_js', 'HTML/CSS/JavaScript'),
        ('react_node', 'React + Node.js'),
        ('vue_express', 'Vue + Express'),
        ('nextjs', 'Next.js Full-Stack'),
        ('django_react', 'Django + React'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='projects')
    name = models.CharField(max_length=255)
    description = models.TextField()
    project_type = models.CharField(max_length=20, choices=PROJECT_TYPES)
    stack = models.CharField(max_length=50, choices=STACK_CHOICES)

    # Features
    has_authentication = models.BooleanField(default=False)
    has_database = models.BooleanField(default=False)
    has_api = models.BooleanField(default=False)
    has_realtime = models.BooleanField(default=False)
    has_payments = models.BooleanField(default=False)

    # AI Generation
    ai_model_used = models.CharField(max_length=100, blank=True)
    generation_prompt = models.TextField(blank=True)
    tokens_used = models.IntegerField(default=0)

    # Status
    status = models.CharField(max_length=20, default='pending', choices=[
        ('pending', 'Pending'),
        ('generating', 'Generating'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ])

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.project_type})"


class GeneratedFile(models.Model):
    FILE_CATEGORIES = [
        ('frontend', 'Frontend'),
        ('backend', 'Backend'),
        ('database', 'Database'),
        ('config', 'Configuration'),
        ('docs', 'Documentation'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='files')
    filename = models.CharField(max_length=255)
    file_path = models.CharField(max_length=500)
    category = models.CharField(max_length=20, choices=FILE_CATEGORIES)
    content = models.TextField()
    language = models.CharField(max_length=50, blank=True)  # python, javascript, html, etc.

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['category', 'filename']

    def __str__(self):
        return f"{self.project.name}/{self.filename}"


class GenerationHistory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='history')
    prompt = models.TextField()
    response = models.TextField()
    model_used = models.CharField(max_length=100)
    tokens_used = models.IntegerField(default=0)
    success = models.BooleanField(default=True)
    error_message = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "Generation histories"


class Deployment(models.Model):
    DEPLOYMENT_PLATFORMS = [
        ('vercel', 'Vercel'),
        ('netlify', 'Netlify'),
        ('heroku', 'Heroku'),
        ('railway', 'Railway'),
        ('render', 'Render'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='deployments')
    platform = models.CharField(max_length=20, choices=DEPLOYMENT_PLATFORMS)
    url = models.URLField(blank=True)
    status = models.CharField(max_length=20, default='pending')
    deployment_logs = models.TextField(blank=True)

    deployed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.project.name} on {self.platform}"