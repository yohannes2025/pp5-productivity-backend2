# productivity_app/tests/test_integration.py
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model

User = get_user_model()


class UserRegistrationIntegrationTest(APITestCase):
    """
    End-to-end integration test for user registration.
    """

    def test_user_registration_success(self):
        url = reverse("productivity_app:register")
        data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "SecurePass123!",
            "confirm_password": "SecurePass123!"
        }

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

        user = User.objects.get(username="newuser")
        self.assertEqual(user.email, "newuser@example.com")
        self.assertTrue(user.check_password("SecurePass123!"))
        self.assertTrue(hasattr(user, "profile"))  # Profile created by signal

    def test_duplicate_email_fails(self):
        User.objects.create_user(
            username="existing", email="taken@example.com", password="pass123"
        )

        url = reverse("productivity_app:register")
        data = {
            "username": "newuser",
            "email": "taken@example.com",
            "password": "SecurePass123!",
            "confirm_password": "SecurePass123!"
        }

        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)

    def test_duplicate_username_fails(self):
        User.objects.create_user(
            username="takenuser", email="user@example.com", password="pass123"
        )

        url = reverse("productivity_app:register")
        data = {
            "username": "takenuser",
            "email": "new@example.com",
            "password": "SecurePass123!",
            "confirm_password": "SecurePass123!"
        }

        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("username", response.data)
