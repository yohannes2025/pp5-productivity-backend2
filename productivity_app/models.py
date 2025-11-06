# productivity_app/models.py
import os
from django.db import models
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save, post_migrate
from django.dispatch import receiver
from django.utils import timezone
from django.core.exceptions import ValidationError

User = get_user_model()

# ----------------------------------------------------------------------
# Profile
# ----------------------------------------------------------------------
class Profile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Profile of {self.user.username}"

@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

# ----------------------------------------------------------------------
# Category – now auto-populated on first migrate
# ----------------------------------------------------------------------
class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name

# Auto-create default categories after migrations
@receiver(post_migrate)
def create_default_categories(sender, **kwargs):
    # ONLY run for our app
    if sender.name != 'productivity_app':
        return

    defaults = ['Development', 'Design', 'Testing', 'Documentation', 'Other']
    for name in defaults:
        Category.objects.get_or_create(name=name)
    print("Default categories ready!")

# ----------------------------------------------------------------------
# Task
# ----------------------------------------------------------------------
class Task(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('done', 'Done'),
    ]
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField()
    due_date = models.DateField(null=True, blank=True)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        related_name='tasks',
        null=True,
        blank=True
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    assigned_users = models.ManyToManyField(User, related_name='assigned_tasks', blank=True)
    created_by = models.ForeignKey(
        User,
        related_name='created_tasks',
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-due_date', '-priority', 'status']

    def clean(self):
        if self.due_date and self.due_date < timezone.now().date():
            raise ValidationError("Due date cannot be in the past.")

    def save(self, *args, **kwargs):
        self.full_clean()  # Ensures validation runs
        super().save(*args, **kwargs)

    @property
    def is_overdue(self):
        if self.due_date and self.status != 'done':
            return timezone.now().date() > self.due_date
        return False

    def __str__(self):
        return self.title

# ----------------------------------------------------------------------
# File Upload
# ----------------------------------------------------------------------
class File(models.Model):
    task = models.ForeignKey(Task, related_name='upload_files', on_delete=models.CASCADE)
    file = models.FileField(upload_to='task_files/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return os.path.basename(self.file.name)