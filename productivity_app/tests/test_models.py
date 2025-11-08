from django.test import TestCase
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import timedelta
from django.contrib.auth import get_user_model
from productivity_app.models import Task, Profile, Category

User = get_user_model()


class TaskModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        """Create shared test data."""
        cls.user = User.objects.create_user(
            username='user1', password='pass123')
        cls.category, _ = Category.objects.get_or_create(name='Development')

    def test_task_creation(self):
        """Test normal task creation."""
        task = Task.objects.create(
            title="Sample Task",
            description="Test description",
            due_date=timezone.now().date() + timedelta(days=1),
            priority="medium",
            category=self.category,
            status="pending",
            created_by=self.user,
        )
        task.assigned_users.set([self.user])

        self.assertEqual(task.title, "Sample Task")
        self.assertFalse(task.is_overdue)
        self.assertEqual(task.category.name, 'Development')

    def test_due_date_cannot_be_past(self):
        """Test that past due_date raises ValidationError."""
        task = Task(
            title="Past Task",
            description="Invalid due date",
            due_date=timezone.now().date() - timedelta(days=1),
            priority="low",
            status="pending",
            created_by=self.user,
            category=self.category,
        )

        with self.assertRaises(ValidationError) as context:
            task.full_clean()

        # Error is under '__all__' because clean() raises ValidationError("msg")
        self.assertIn('__all__', context.exception.message_dict)
        errors = context.exception.message_dict['__all__']
        self.assertIn("Due date cannot be in the past.", errors)

    def test_profile_created_on_user_creation(self):
        """Test Profile is auto-created."""
        new_user = User.objects.create_user(
            username='user2', password='pass123')
        self.assertTrue(hasattr(new_user, 'profile'))
        self.assertIsNotNone(new_user.profile)
        self

    def test_is_overdue_property(self):
        """Test is_overdue logic WITHOUT triggering save() validation."""
        today = timezone.now().date()

        # 1. Overdue task (pending + past due) — create without save
        overdue_task = Task(
            title="Overdue Task",
            description="This is late",
            due_date=today - timedelta(days=1),
            priority="high",
            category=self.category,
            status="pending",
            created_by=self.user,
        )
        # Bypass full_clean() and save() — we only want to test the property
        overdue_task._state.adding = False  # Simulate saved object
        overdue_task._state.db = 'default'
        self.assertTrue(overdue_task.is_overdue)

        # 2. Future task — safe to save
        future_task = Task.objects.create(
            title="Future Task",
            description="Due tomorrow",
            due_date=today + timedelta(days=1),
            priority="low",
            category=self.category,
            status="pending",
            created_by=self.user,
        )
        self.assertFalse(future_task.is_overdue)

        # 3. Done task (even if past due) — bypass save
        done_task = Task(
            title="Done Task",
            description="Completed",
            due_date=today - timedelta(days=1),
            priority="low",
            category=self.category,
            status="done",
            created_by=self.user,
        )
        done_task._state.adding = False
        done_task._state.db = 'default'
        self.assertFalse(done_task.is_overdue)

        # 4. No due date — safe to save
        no_due_task = Task.objects.create(
            title="No Due Date",
            description="No deadline",
            due_date=None,
            priority="medium",
            category=self.category,
            status="pending",
            created_by=self.user,
        )
        self.assertFalse(no_due_task.is_overdue)
