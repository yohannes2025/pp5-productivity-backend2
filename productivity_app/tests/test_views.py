# productivity_app/tests/test_views.py
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model
from productivity_app.models import Task, Profile, Category

User = get_user_model()


class BaseAPITestCase(TestCase):
    """Base test case with user and auth client setup."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="password123"
        )

    def authenticate(self):
        url = reverse("productivity_app:login")
        data = {"email": self.user.email, "password": "password123"}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        token = response.data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")


# --- Authentication Tests ---
class AuthenticationTests(BaseAPITestCase):
    def test_user_registration(self):
        url = reverse("productivity_app:register")
        data = {
            "username": "newuser",
            "email": "new@example.com",
            "password": "securepass123",
            "confirm_password": "securepass123"
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("access", response.data)
        self.assertTrue(User.objects.filter(username="newuser").exists())

    def test_user_login(self):
        url = reverse("productivity_app:login")
        data = {"email": "test@example.com", "password": "password123"}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)


# --- User API Tests ---
class UserAPITests(BaseAPITestCase):
    def test_users_list_requires_auth(self):
        url = reverse("productivity_app:users-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_users_list_authenticated(self):
        self.authenticate()
        url = reverse("productivity_app:users-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(
            any(u["username"] == self.user.username for u in response.data)
        )

    def test_user_detail_update(self):
        self.authenticate()
        url = reverse("productivity_app:user-detail")
        data = {"username": "updateduser"}
        response = self.client.patch(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, "updateduser")


# --- Profile API Tests ---
class ProfileAPITests(BaseAPITestCase):
    def test_profile_list(self):
        url = reverse("productivity_app:profile-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(
            any("user_name" in profile for profile in response.data)
        )

    def test_profile_update_only_self(self):
        """Profile cannot update username; API should allow updating other fields only."""
        self.authenticate()
        profile = self.user.profile
        url = reverse("productivity_app:profile-detail", args=[profile.id])
        # will not actually update username
        data = {"user_name": "UpdatedName"}
        response = self.client.patch(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        profile.refresh_from_db()
        # Username should remain unchanged
        self.assertEqual(profile.user.username, "testuser")


# --- Task API Tests ---
class TaskAPITests(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        # Use get_or_create – avoids UNIQUE constraint error
        self.category, _ = Category.objects.get_or_create(name="Development")

        self.task = Task.objects.create(
            title="Test Task",
            description="Task description",
            due_date=timezone.now().date() + timedelta(days=1),
            priority="medium",
            status="pending",
            created_by=self.user,
            category=self.category
        )
        self.task.assigned_users.set([self.user])

    def test_task_list_authenticated(self):
        self.authenticate()
        url = reverse("productivity_app:task-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(
            any(t["title"] == self.task.title for t in response.data)
        )

    def test_task_create(self):
        self.authenticate()
        url = reverse("productivity_app:task-list")
        data = {
            "title": "New Task",
            "description": "Some description",
            "due_date": str(timezone.now().date() + timedelta(days=2)),
            "priority": "low",
            "status": "pending",
            "category": self.category.id
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Task.objects.filter(title="New Task").exists())

    def test_task_update_only_if_assigned(self):
        self.authenticate()
        url = reverse("productivity_app:task-detail", args=[self.task.id])
        data = {"title": "Updated Task"}
        response = self.client.patch(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.task.refresh_from_db()
        self.assertEqual(self.task.title, "Updated Task")

    def test_task_delete_only_if_assigned(self):
        self.authenticate()
        url = reverse("productivity_app:task-detail", args=[self.task.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Task.objects.filter(id=self.task.id).exists())
