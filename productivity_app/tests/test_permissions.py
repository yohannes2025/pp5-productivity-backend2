# productivity_app/tests/test_permissions.py
from django.test import TestCase
from django.contrib.auth import get_user_model
from productivity_app.models import Task, Profile, Category
from productivity_app.permissions import (
    IsAssignedOrReadOnly,
    IsSelfOrReadOnly,
    IsOwnerOrReadOnly,
)
from rest_framework.test import APIRequestFactory
from rest_framework.views import APIView

User = get_user_model()


class DummyView(APIView):
    """A dummy view for testing permissions."""
    pass


class PermissionTests(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(
            username="user1", email="user1@example.com", password="password123"
        )
        self.user2 = User.objects.create_user(
            username="user2", email="user2@example.com", password="password123"
        )

        # Use get_or_create – avoids UNIQUE constraint error
        self.category, _ = Category.objects.get_or_create(name="Testing")

        # Task assigned only to user1
        self.task = Task.objects.create(
            title="Test Task",
            description="Task description",
            due_date="2100-01-01",
            priority="high",
            status="pending",
            created_by=self.user1,
            category=self.category,
        )
        self.task.assigned_users.set([self.user1])

        # Profiles – use get_or_create to be safe
        self.profile1, _ = Profile.objects.get_or_create(user=self.user1)
        self.profile2, _ = Profile.objects.get_or_create(user=self.user2)

        self.factory = APIRequestFactory()

    # --- IsAssignedOrReadOnly tests ---
    def test_is_assigned_or_readonly_safe_methods(self):
        permission = IsAssignedOrReadOnly()
        request = self.factory.get("/tasks/")
        request.user = self.user2
        self.assertTrue(permission.has_permission(request, DummyView()))
        self.assertTrue(
            permission.has_object_permission(request, DummyView(), self.task)
        )

    def test_is_assigned_or_readonly_non_safe_methods(self):
        permission = IsAssignedOrReadOnly()
        request = self.factory.patch("/tasks/")
        request.user = self.user2
        self.assertTrue(permission.has_permission(request, DummyView()))
        self.assertFalse(
            permission.has_object_permission(request, DummyView(), self.task)
        )
        request.user = self.user1
        self.assertTrue(
            permission.has_object_permission(request, DummyView(), self.task)
        )

    # --- IsSelfOrReadOnly tests ---
    def test_is_self_or_readonly(self):
        permission = IsSelfOrReadOnly()
        request = self.factory.patch("/users/")
        request.user = self.user1
        # Can modify self
        self.assertTrue(
            permission.has_object_permission(request, DummyView(), self.user1)
        )
        # Cannot modify other
        self.assertFalse(
            permission.has_object_permission(request, DummyView(), self.user2)
        )
        # Safe methods
        request = self.factory.get("/users/")
        request.user = self.user2
        self.assertTrue(
            permission.has_object_permission(request, DummyView(), self.user1)
        )

    # --- IsOwnerOrReadOnly tests ---
    def test_is_owner_or_readonly(self):
        permission = IsOwnerOrReadOnly()
        request = self.factory.patch("/profiles/")
        request.user = self.user1
        # Can modify own profile
        self.assertTrue(
            permission.has_object_permission(
                request, DummyView(), self.profile1)
        )
        # Cannot modify other's profile
        self.assertFalse(
            permission.has_object_permission(
                request, DummyView(), self.profile2)
        )
        # Safe methods
        request = self.factory.get("/profiles/")
        request.user = self.user2
        self.assertTrue(
            permission.has_object_permission(
                request, DummyView(), self.profile1)
        )
