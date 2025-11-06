# # productivity_app/models.py
# import os
# from django.db import models
# from django.contrib.auth.models import User
# from django.db.models.signals import post_save
# from django.core.exceptions import ValidationError
# from django.utils import timezone
# from django.contrib.auth import get_user_model

# User = get_user_model()


# class Profile(models.Model):
#     """
#     Extends the built-in User model with additional profile information.
#     Uses a OneToOneField to link each Profile to a User.
#     """
#     user = models.OneToOneField(
#         User,
#         on_delete=models.CASCADE,
#         null=True,
#         blank=True,
#         related_name='profile'
#     )
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

#     class Meta:
#         ordering = ['-created_at']

#     def __str__(self):
#         return f"Profile of {self.user.username}" if self.user else "Profile"


# # Signal handler for creating Profile
# def create_profile(sender, instance, created, **kwargs):
#     if created:
#         Profile.objects.create(user=instance)


# # Connect the signal to the User model
# post_save.connect(create_profile, sender=User)


# class Category(models.Model):
#     name = models.CharField(max_length=100)

#     def __str__(self):
#         return self.name


# class Task(models.Model):
#     """
#     Represents a task that can be assigned to one or more users.
#     Includes metadata like due date, priority, and optional file attachments.
#     """
#     # Choices for the 'status' field
#     STATUS_CHOICES = [
#         ('pending', 'Pending'),
#         ('in_progress', 'In Progress'),
#         ('done', 'Done'),
#     ]

#     # Choices for the 'category' field
#     CATEGORY_CHOICES = [
#         ('development', 'Development'),
#         ('design', 'Design'),
#         ('testing', 'Testing'),
#         ('documentation', 'Documentation'),
#         ('other', 'Other'),
#     ]

#     # Choices for the 'property' field
#     PRIORITY_CHOICES = [
#         ('low', 'Low'),
#         ('medium', 'Medium'),
#         ('high', 'High'),
#     ]

#     title = models.CharField(max_length=255)
#     description = models.TextField()
#     due_date = models.DateField(null=True, blank=True)  # optional due date
#     priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES)
#     category = models.ForeignKey(
#         Category,
#         on_delete=models.SET_NULL,
#         related_name='tasks',
#         blank=True,
#         null=True
#     )
#     status = models.CharField(
#         max_length=20,
#         choices=STATUS_CHOICES,
#         default='pending'
#     )
#     assigned_users = models.ManyToManyField(
#         User, related_name='assigned_tasks'
#     )
#     created_by = models.ForeignKey(
#         User,
#         related_name='created_tasks',
#         null=True,
#         blank=True,
#         on_delete=models.SET_NULL
#     )
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

#     class Meta:
#         ordering = ['due_date', 'priority', 'status']

#     def clean(self):
#         # Validate that due_date is not in the past
#         if self.due_date and self.due_date < timezone.now().date():
#             raise ValidationError("Due date cannot be in the past.")

#     def save(self, *args, **kwargs):
#         # The clean() method is not called here, as it's typically
#         # handled by forms or serializers before a save operation.
#         super().save(*args, **kwargs)

#     @property
#     def is_overdue(self):
#         """Checks if the task's due date is in the past."""
#         if self.due_date:
#             return (
#                 timezone.now().date() > self.due_date
#                 and self.status != 'done'
#             )

#         return False

#     def __str__(self):
#         return self.title


# class File(models.Model):
#     """Represents a file uploaded for a Task."""
#     task = models.ForeignKey(
#         Task, related_name='upload_files', on_delete=models.CASCADE
#     )
#     file = models.FileField(upload_to='task_files')
#     uploaded_at = models.DateTimeField(auto_now_add=True)

#     def __str__(self):
#         # Return only the filename, not the full path
#         return os.path.basename(self.file.name)


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
    if sender.name == 'productivity_app':  # Only run for this app
        defaults = ['Development', 'Design', 'Testing', 'Documentation', 'Other']
        created_count = 0
        for name in defaults:
            obj, created = Category.objects.get_or_create(name=name)
            if created:
                created_count += 1
        if created_count:
            print(f"Created {created_count} default categories.")

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