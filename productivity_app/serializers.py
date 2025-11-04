# productivity_app/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from .models import Profile, Task, File, Category

User = get_user_model()


User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    """Serializer for user registration."""
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'confirm_password')
        extra_kwargs = {
            'username': {'required': True, 'label': 'Name'},
            'email': {'required': True},
            'password': {'write_only': True}
        }

    def validate(self, attrs):
        errors = {}

        # Check passwords match
        if attrs['password'] != attrs['confirm_password']:
            errors['password'] = "Passwords must match."

        # Validate password strength
        user_data = {
            'username': attrs['username'],
            'email': attrs['email']
        }
        try:
            validate_password(attrs['password'], user=User(**user_data))
        except serializers.ValidationError as e:
            errors['password'] = " ".join(e.messages)

        # Check if email already exists
        if User.objects.filter(email=attrs['email']).exists():
            errors['email'] = "A user with this email already exists."

        # Check if username already exists
        if User.objects.filter(username=attrs['username']).exists():
            errors['username'] = "A user with this username already exists."

        if errors:
            raise serializers.ValidationError(errors)

        return attrs

    def create(self, validated_data):
        # Remove confirm_password before creating user
        validated_data.pop('confirm_password', None)
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user


class LoginSerializer(serializers.Serializer):
    """Serializer for user login using email."""
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if not email or not password:
            raise serializers.ValidationError(
                'Email and password are required.', code='authorization')

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError(
                'Invalid credentials.', code='authorization')

        if not user.check_password(password):
            raise serializers.ValidationError(
                'Invalid credentials.', code='authorization')

        if not user.is_active:
            raise serializers.ValidationError(
                'User account is disabled.', code='authorization')

        attrs['user'] = user
        return attrs


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email"]


class FileSerializer(serializers.ModelSerializer):
    """Serializer for file uploads."""

    class Meta:
        model = File
        fields = ['id', 'file']


class ProfileSerializer(serializers.ModelSerializer):
    """Serializer for user profile."""
    # Use StringRelatedField to access the related User's username and email
    user_name = serializers.CharField(source='user.username', read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = Profile
        fields = ['id', 'user_name', 'user_email', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']


class TaskSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating a Task."""
    assigned_users = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        many=True,
        required=False
    )
    category = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        required=True
    )
    upload_files = FileSerializer(many=True, read_only=True)

    class Meta:
        model = Task
        fields = [
            'id', 'title', 'description', 'due_date', 'priority',
            'category', 'status', 'assigned_users', 'upload_files',
            'created_at', 'updated_at', 'is_overdue',
        ]
        read_only_fields = ['created_at', 'updated_at', 'is_overdue']

    def create(self, validated_data):
        assigned_users_data = validated_data.pop('assigned_users', [])
        task = Task.objects.create(**validated_data)
        task.assigned_users.set(assigned_users_data)
        return task

    def update(self, instance, validated_data):
        assigned_users_data = validated_data.pop('assigned_users', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if assigned_users_data is not None:
            instance.assigned_users.set(assigned_users_data)
        instance.save()
        return instance


class TaskListSerializer(serializers.ModelSerializer):
    """Serializer for listing tasks with summary info."""
    category = serializers.StringRelatedField()

    class Meta:
        model = Task
        fields = ['id', 'title', 'description', 'due_date', 'priority',
                  'category', 'status', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']


class TaskDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed view of a task."""
    assigned_users = UserSerializer(many=True, read_only=True)
    assigned_user_ids = serializers.PrimaryKeyRelatedField(
        source='assigned_users',
        queryset=User.objects.all(),
        many=True,
        write_only=True,
    )
    category = serializers.StringRelatedField()
    upload_files = FileSerializer(many=True, read_only=True)

    class Meta:
        model = Task
        fields = ['id', 'title', 'description', 'due_date', 'priority',
                  'category', 'status', 'assigned_users', 'assigned_user_ids',
                  'upload_files', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']


class CategorySerializer(serializers.ModelSerializer):
    """
    Serializer for the Category model.
    """
    class Meta:
        model = Category
        fields = ['id', 'name']
