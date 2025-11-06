# productivity_app/views.py
from rest_framework import generics, viewsets, views, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import (
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
    AllowAny,
)

from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import permissions
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

# Django imports
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.db import transaction

# Local application imports
from .models import Profile, Task, Category, File  # Added File to imports
from .permissions import IsAssignedOrReadOnly, IsSelfOrReadOnly
from .serializers import (
    TaskSerializer,
    ProfileSerializer,
    RegisterSerializer,
    LoginSerializer,
    UserSerializer,
    CategorySerializer
)

User = get_user_model()


class RegisterViewSet(generics.CreateAPIView):
    """
    Handles user registration.
    """
    serializer_class = RegisterSerializer

    def post(self, request, *args, **kwargs):
        """
        Handle POST request for user registration.
        Uses a transaction to ensure atomicity (user and profile creation).
        """
        with transaction.atomic():
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            # Call perform_create to create the user
            user = self.perform_create(serializer)

            refresh = RefreshToken.for_user(user)
            response_data = {
                'message': 'User registered successfully',
                'user_id': user.id,
                'username': user.username,
                'email': user.email,
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
            return Response(response_data, status=status.HTTP_201_CREATED)

    def perform_create(self, serializer):
        """
        Custom perform_create to return the created user instance.
        """
        return serializer.save()


class LoginViewSet(views.APIView):
    """
    Handles user login and token generation.
    """

    def post(self, request, *args, **kwargs):
        """
        Handle POST request for user login.
        """
        serializer = LoginSerializer(
            data=request.data, context={'request': request})

        serializer.is_valid(raise_exception=True)

        # If valid, the user is in validated_data
        user = serializer.validated_data['user']

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)

        # Return tokens in the response
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        }, status=status.HTTP_200_OK)


class UsersListAPIView(views.APIView):
    """
    A view to list all users.
    Requires authentication to see the list.
    """
    permission_classes = [
        IsAuthenticated]  # Only authenticated users can list users

    def get(self, request):
        users = User.objects.all()
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class UserDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    Allows users to retrieve, update, or delete their own profile.
    """
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated, IsSelfOrReadOnly]

    def get_object(self):
        # Return the current authenticated user instance only
        return self.request.user


class ProfileViewSet(viewsets.ModelViewSet):
    """
    A viewset for viewing and editing user profiles.
    Public can view all profiles. Authenticated users
    can edit/delete only their own profile.
    """
    serializer_class = ProfileSerializer
    queryset = Profile.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        return Profile.objects.all()

    def get_object(self):
        obj = super().get_object()
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            if self.request.user != obj.user:
                raise PermissionDenied("You can only modify your own profile.")
        return obj

    def perform_update(self, serializer):
        if self.request.user != serializer.instance.user:
            raise PermissionDenied("You can only update your own profile.")
        serializer.save()

    def perform_destroy(self, instance):
        if self.request.user != instance.user:
            raise PermissionDenied("You can only delete your own profile.")
        instance.delete()


class TaskViewSet(viewsets.ModelViewSet):
    """
    A viewset for viewing, creating, updating, and deleting Task instances.
    Users can only see and edit tasks where they are assigned.
    """
    serializer_class = TaskSerializer
    # Only authenticated users can interact
    permission_classes = [IsAssignedOrReadOnly]
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            return Task.objects.filter(assigned_users=user).distinct()
        return Task.objects.all()

    def perform_create(self, serializer):
        """
        Automatically assign the logged-in user to the created task.
        If assigned_users are not provided in the request,
        assign the creating user.
        """
        assigned_users_data = serializer.validated_data.get(
            'assigned_users', [])
        # Save the task instance, ensuring the creator is set
        task = serializer.save(created_by=self.request.user)

        # Ensure the creating user is assigned to the task
        if not assigned_users_data:
            task.assigned_users.set([self.request.user])

        # Check for and handle file uploads
        files = self.request.FILES.getlist('files')
        if files:
            for file in files:
                File.objects.create(task=task, file=file)

    def perform_update(self, serializer):
        """
        Override perform_update to ensure the logged-in user
        is assigned to the task before allowing the update.
        """
        task = self.get_object()
        # Check if the requesting user is assigned to the task
        if self.request.user not in task.assigned_users.all():
            raise PermissionDenied(
                "You do not have permission to edit this task.")

        serializer.save()

    def perform_destroy(self, instance):
        """
        Override perform_destroy to ensure the logged-in user
        is assigned to the task before allowing deletion.
        """
        # Check if the requesting user is assigned to the task
        if self.request.user not in instance.assigned_users.all():
            raise PermissionDenied(
                "You do not have permission to delete this task.")
        instance.delete()


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    A viewset for viewing Categories.
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]
    authentication_classes = []

