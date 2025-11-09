# productivity_app/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from .models import Profile, Task, File, Category
import cloudinary.uploader

User = get_user_model()


# ──────────────────────────────
#  Register / Login
# ──────────────────────────────
class RegisterSerializer(serializers.ModelSerializer):
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ("username", "email", "password", "confirm_password")
        extra_kwargs = {
            "username": {"required": True},
            "email": {"required": True},
            "password": {"write_only": True},
        }

    def validate(self, attrs):
        if attrs["password"] != attrs["confirm_password"]:
            raise serializers.ValidationError(
                {"password": "Passwords must match."})
        attrs.pop("confirm_password")
        validate_password(attrs["password"], User(**attrs))
        if User.objects.filter(email=attrs["email"]).exists():
            raise serializers.ValidationError(
                {"email": "Email already taken."})
        if User.objects.filter(username=attrs["username"]).exists():
            raise serializers.ValidationError(
                {"username": "Username already taken."})
        return attrs

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        try:
            user = User.objects.get(email=attrs["email"])
        except User.DoesNotExist:
            raise serializers.ValidationError("Invalid credentials.")
        if not user.check_password(attrs["password"]):
            raise serializers.ValidationError("Invalid credentials.")
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


# ──────────────────────────────
#  File – Cloudinary Upload
# ──────────────────────────────
class FileSerializer(serializers.ModelSerializer):
    file = serializers.FileField(write_only=True, required=False)
    file_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = File
        fields = ["id", "file", "file_url", "uploaded_at"]

    def get_file_url(self, obj):
        return obj.file.url if obj.file else None

    def create(self, validated_data):
        task = self.context["task"]
        uploaded_file = validated_data.pop("file", None)
        if uploaded_file:
            result = cloudinary.uploader.upload(
                uploaded_file, folder="task_files")
            cloudinary_url = result["secure_url"]
            file_obj = File.objects.create(task=task, file=cloudinary_url)
        else:
            file_obj = File.objects.create(task=task)
        return file_obj


# ──────────────────────────────
#  Category
# ──────────────────────────────
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name"]


# ──────────────────────────────
#  Task – Full Create / Update (FIXED: full_clean added)
# ──────────────────────────────
class TaskSerializer(serializers.ModelSerializer):
    assigned_users = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), many=True, required=False
    )
    category = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all()
    )
    upload_files = FileSerializer(many=True, read_only=True)
    new_files = serializers.ListField(
        child=serializers.FileField(),
        write_only=True,
        required=False
    )

    class Meta:
        model = Task
        fields = [
            "id", "title", "description", "due_date", "priority",
            "category", "status", "assigned_users", "upload_files",
            "new_files", "created_at", "updated_at", "is_overdue"
        ]
        read_only_fields = ["created_at", "updated_at", "is_overdue"]

    def create(self, validated_data):
        new_files = validated_data.pop("new_files", [])
        users = validated_data.pop("assigned_users", [])

        # Create task instance
        task = Task(**validated_data)

        # Run model validation (past due_date, etc.)
        task.full_clean()

        task.save()
        task.assigned_users.set(users)

        # Handle file uploads
        for f in new_files:
            FileSerializer(context={"task": task}).create({"file": f})

        return task

    def update(self, instance, validated_data):
        new_files = validated_data.pop("new_files", [])
        users = validated_data.pop("assigned_users", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        # Validate before saving
        instance.full_clean()

        instance.save()

        if users is not None:
            instance.assigned_users.set(users)

        for f in new_files:
            FileSerializer(context={"task": instance}).create({"file": f})

        return instance


# ──────────────────────────────
#  List & Detail
# ──────────────────────────────
class TaskListSerializer(serializers.ModelSerializer):
    category = serializers.CharField(source="category.name")

    class Meta:
        model = Task
        fields = ["id", "title", "description", "due_date", "priority",
                  "category", "status", "created_at", "updated_at"]


class TaskDetailSerializer(serializers.ModelSerializer):
    assigned_users = UserSerializer(many=True)
    assigned_user_ids = serializers.PrimaryKeyRelatedField(
        source="assigned_users",
        queryset=User.objects.all(),
        many=True,
        write_only=True
    )
    category = serializers.StringRelatedField()
    upload_files = FileSerializer(many=True)

    class Meta:
        model = Task
        fields = [
            "id", "title", "description", "due_date", "priority",
            "category", "status", "assigned_users", "assigned_user_ids",
            "upload_files", "created_at", "updated_at"
        ]
