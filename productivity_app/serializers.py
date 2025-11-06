# productivity_app/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from .models import Profile, Task, File, Category

User = get_user_model()


# ──────────────────────────────
#  Register / Login
# ──────────────────────────────
class RegisterSerializer(serializers.ModelSerializer):
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ("username", "email", "password", "confirm_password")
        extra_kwargs = {
            "username": {"required": True, "label": "Name"},
            "email": {"required": True},
            "password": {"write_only": True},
        }

    def validate(self, attrs):
        errors = {}
        
        # 1. Check if passwords match
        if attrs["password"] != attrs["confirm_password"]:
            errors["password"] = "Passwords must match."

        # 2. Pop the non-model field for password validation
        #    We must save it temporarily and remove it from attrs before calling User(**attrs)
        password_to_validate = attrs["password"]
        confirm_password = attrs.pop("confirm_password")  # FIX: Remove 'confirm_password'

        # 3. Perform password strength validation
        try:
            # Pass only fields that exist on the User model
            validate_password(password_to_validate, user=User(**attrs))
        except serializers.ValidationError as e:
            errors["password"] = " ".join(e.messages)
        
        # NOTE: Re-insert 'confirm_password' into attrs if it's needed later in the validation
        # or for raising a combined error. Since you use it only for validation checks, 
        # it's usually safer to re-insert it if validation *passed* before throwing
        # the ValidationError, but for simplicity here, we continue checks.

        # 4. Check for existing users
        if User.objects.filter(email=attrs["email"]).exists():
            errors["email"] = "Email already taken."
        if User.objects.filter(username=attrs["username"]).exists():
            errors["username"] = "Username already taken."

        if errors:
            # Re-add 'confirm_password' to attrs before raising if needed 
            # (though not strictly necessary here since the function exits)
            attrs["confirm_password"] = confirm_password 
            raise serializers.ValidationError(errors)
            
        # If no errors, re-add it back for the 'create' method to pop it again (or handle it cleanly)
        # OR better yet, just let the popped state remain, since 'create' will pop it again. 
        # For simplicity and correctness with the existing 'create' method:
        attrs["confirm_password"] = confirm_password # Re-add to satisfy the create method's pop logic
        return attrs

    def create(self, validated_data):
        # The 'confirm_password' is popped here again (or already popped in validate)
        # It's cleaner to handle the pop in one place, but this works with the fix above.
        validated_data.pop("confirm_password", None)
        return User.objects.create_user(**validated_data)


class LoginSerializer(serializers.Serializer):
# ... (rest of the LoginSerializer remains the same)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs["email"]
        password = attrs["password"]
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError("Invalid credentials.", code="authorization")

        if not user.check_password(password):
            raise serializers.ValidationError("Invalid credentials.", code="authorization")
        if not user.is_active:
            raise serializers.ValidationError("Account disabled.", code="authorization")

        attrs["user"] = user
        return attrs


# ──────────────────────────────
#  User / Profile
# ──────────────────────────────
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email"]


class ProfileSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.username", read_only=True)
    user_email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = Profile
        fields = ["id", "user_name", "user_email", "created_at", "updated_at"]
        read_only_fields = ["created_at", "updated_at"]


# ──────────────────────────────
#  File
# ──────────────────────────────
class FileSerializer(serializers.ModelSerializer):
    class Meta:
        model = File
        fields = ["id", "file"]


# ──────────────────────────────
#  Category
# ──────────────────────────────
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name"]


# ──────────────────────────────
#  Task – Full Create / Update
# ──────────────────────────────
class TaskSerializer(serializers.ModelSerializer):
    assigned_users = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), many=True, required=False
    )
    category = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), required=True
    )
    upload_files = FileSerializer(many=True, read_only=True)

    class Meta:
        model = Task
        fields = [
            "id",
            "title",
            "description",
            "due_date",
            "priority",
            "category",
            "status",
            "assigned_users",
            "upload_files",
            "created_at",
            "updated_at",
            "is_overdue",
        ]
        read_only_fields = ["created_at", "updated_at", "is_overdue"]

    def create(self, validated_data):
        users = validated_data.pop("assigned_users", [])
        task = Task.objects.create(**validated_data)
        task.assigned_users.set(users)
        return task

    def update(self, instance, validated_data):
        users = validated_data.pop("assigned_users", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if users is not None:
            instance.assigned_users.set(users)
        instance.save()
        return instance


# ──────────────────────────────
#  Task – List View (exactly what you asked for)
# ──────────────────────────────
class TaskListSerializer(serializers.ModelSerializer):
    category = serializers.CharField(source="category.name")  # ← THIS LINE

    class Meta:
        model = Task
        fields = [
            "id",
            "title",
            "description",
            "due_date",
            "priority",
            "category",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


# ──────────────────────────────
#  Task – Detail View
# ──────────────────────────────
class TaskDetailSerializer(serializers.ModelSerializer):
    assigned_users = UserSerializer(many=True, read_only=True)
    assigned_user_ids = serializers.PrimaryKeyRelatedField(
        source="assigned_users",
        queryset=User.objects.all(),
        many=True,
        write_only=True,
    )
    category = serializers.StringRelatedField()
    upload_files = FileSerializer(many=True, read_only=True)

    class Meta:
        model = Task
        fields = [
            "id",
            "title",
            "description",
            "due_date",
            "priority",
            "category",
            "status",
            "assigned_users",
            "assigned_user_ids",
            "upload_files",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]