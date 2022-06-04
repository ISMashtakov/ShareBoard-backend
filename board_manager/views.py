from django.http import HttpResponse, JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt

from authentication.serializers import UserSerializer
from helpers.helper import catch_view_exception
from .logger import boards_logger
from .board_manager_backend import BoardManager
from .exceptions import BoardManagerException
from .serializers import (
    UserBoardsSerializer, BoardWithoutContentSerializer
)
from .models import UserBoards, Access


@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAuthenticated])
@catch_view_exception(['board_type'], boards_logger)
def create_board(request):
    board = BoardManager.create_board("Untitled",
                                      request.data['board_type'],
                                      request.user,
                                      request.data.get('prev_board_id'))
    serializer = BoardWithoutContentSerializer(board)
    return JsonResponse(serializer.data, status=status.HTTP_201_CREATED)


@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAuthenticated])
@catch_view_exception(['board_id'], boards_logger)
def delete_board(request):
    try:
        BoardManager.delete_board(request.data['board_id'],
                                  request.user)
        return HttpResponse(status=status.HTTP_204_NO_CONTENT)
    except BoardManagerException as e:
        return HttpResponse(content=e.message, status=e.response_status)


@csrf_exempt
@api_view(['GET'])
@permission_classes([IsAuthenticated])
@catch_view_exception([], boards_logger)
def my_boards(request):
    boards = BoardManager.get_user_boards(request.user)
    serializer = UserBoardsSerializer(boards, many=True)
    for row in serializer.data:
        owner = UserBoards.objects.get(board=row["id"], access=Access.OWNER)
        row["owner"] = UserSerializer(owner).data
    return JsonResponse(serializer.data, status=status.HTTP_200_OK, safe=False)


@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAuthenticated])
@catch_view_exception(['board_id'], boards_logger)
def open_board(request):
    try:
        board_link = BoardManager.generate_link(request.data['board_id'])
        return HttpResponse(board_link, status=status.HTTP_200_OK)
    except BoardManagerException as e:
        return HttpResponse(content=e.message, status=e.response_status)


@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAuthenticated])
@catch_view_exception(['board_id'], boards_logger)
def leave_board(request):
    try:
        BoardManager.leave_board(request.data['board_id'],
                                 request.user)
        return HttpResponse(status=status.HTTP_204_NO_CONTENT)
    except BoardManagerException as e:
        return HttpResponse(content=e.message, status=e.response_status)
