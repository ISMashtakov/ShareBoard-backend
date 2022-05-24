from django.urls import path
from .views import (
    create_file, delete_file, my_files, open_file, leave_file
)


urlpatterns = [
    path('create_file/', create_file),
    path('delete_file/', delete_file),
    path('my', my_files),
    path('open_file/', open_file),
    path('leave_file/', leave_file),
]
