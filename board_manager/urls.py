from django.urls import path
from .views import (
    create_board, delete_board, my_boards, open_board, leave_board, get_board_columns
)


urlpatterns = [
    path('create_board/', create_board),
    path('delete_board/', delete_board),
    path('my', my_boards),
    path('open_board/', open_board),
    path('leave_board/', leave_board),
    path('get_board_columns/', get_board_columns),
]
