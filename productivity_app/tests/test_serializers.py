# productivity_app/tests/test_serializers.py
from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory
from productivity_app.models import Task, Category
from productivity_app.serializers import TaskSerializer, RegisterSerializer

User = get_user_model()
factory = APIRequestFactory()          # needed for request context


class TaskSerializerTests[TestCase]:
    @classmethod
    def setUpTestData(cls):
        """Reusable objects – safely avoid duplicate categories."""
        cls.user = User.objects.create_user(
            username='user1', password='pass123')
        cls.category, _ = Category.objects.get_or_create(name='Development')

    def setUp(self):
        """Provide request context for every test."""
        self.request = factory.get('/')
        self.request.user = self.user

    # ------------------------------------------------------------
    # 1. Valid data → serializer saves correctly
    # ------------------------------------------------------------
    def test_task_serializer_valid_data(self):
        data = {
            'title': 'Task',
            'description': 'Details',
            'due_date': (timezone.now().date() + timedelta(days=1)).isoformat(),
            'priority': 'high',
            'category': self.category.id,
            'status': 'pending',
            'assigned_users': [self.user.id],
        }

        serializer = TaskSerializer(
            data=data, context={'request': self.request})
        self.assertTrue(serializer.is_valid(), serializer.errors)

        task = serializer.save(created_by=self.user)
        self.assertEqual(task.title, 'Task')
        self.assertEqual(task.assigned_users.first(), self.user)

    # ------------------------------------------------------------
    # 2. Past due_date → serializer REJECTS (model validation)
    # ------------------------------------------------------------
    def test_task_serializer_due_date_validation(self):
        data = {
            'title': 'Past Task',
            'description': 'Invalid',
            'due_date': (timezone.now().date() - timedelta(days=1)).isoformat(),
            'priority': 'low',
            'category': self.category.id,
            'status': 'pending',
            'assigned_users': [self.user.id],
        }

        serializer = TaskSerializer(
            data=data, context={'request': self.request})
        self.assertFalse(serializer.is_valid(),
                         "Serializer should reject past due_date")

        # Model clean() error ends up in non_field_errors
        self.assertIn('non_field_errors', serializer.errors)
        err_msg = str(serializer.errors['non_field_errors'][0]).lower()
        self.assertIn('past', err_msg)


class RegisterSerializerTests(TestCase):
    # ------------------------------------------------------------
    # 3. Valid registration
    # ------------------------------------------------------------
    def test_register_serializer_valid_data(self):
        data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'password123!',
            'confirm_password': 'password123!'
        }
        serializer = RegisterSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

        user = serializer.save()
        self.assertEqual(user.username, 'testuser')
        self.assertTrue(user.check_password('password123!'))

    # ------------------------------------------------------------
    # 4. Password too short
    # ------------------------------------------------------------
    def test_register_serializer_invalid_password(self):
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'short',
            'confirm_password': 'short'
        }
        serializer = RegisterSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('non_field_errors', serializer.errors)

    # ------------------------------------------------------------
    # 5. Duplicate username / email
    # ------------------------------------------------------------
    def test_register_serializer_existing_user(self):
        User.objects.create_user(
            username='existinguser', email='test@example.com', password='password123!'
        )

        # duplicate username
        data1 = {
            'username': 'existinguser',
            'email': 'new@example.com',
            'password': 'password123!',
            'confirm_password': 'password123!'
        }
        s1 = RegisterSerializer(data=data1)
        self.assertFalse(s1.is_valid())
        self.assertIn('username', s1.errors)

        # duplicate email
        data2 = {
            'username': 'newuser2',
            'email': 'test@example.com',
            'password': 'password123!',
            'confirm_password': 'password123!'
        }
        s2 = RegisterSerializer(data=data2)
        self.assertFalse(s2.is_valid())
        self.assertIn('email', s2.errors)
