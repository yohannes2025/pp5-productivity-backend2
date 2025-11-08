# drf_api/urls.py
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse


def home(request):
    return JsonResponse({"message": "Welcome to the Productivity App API"})


urlpatterns = [
    path('', home),  # Root path handler
    path('admin/', admin.site.urls),
    path('', include('productivity_app.urls', namespace='productivity_app')),
]
