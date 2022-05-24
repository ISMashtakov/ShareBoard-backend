from django.urls import path

from .views import (
    check_username, check_email
)

urlpatterns = [
    path('check_username/', check_username),
    path('check_email/', check_email),
]
