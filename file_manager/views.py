from django.http import HttpResponse, JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt

from helpers.helper import catch_view_exception
from .logger import file_manager_logger
from .file_manager_backend import FileManager
from .exceptions import FileManageException
from .serializers import (
    UserFilesSerializer, FileWithoutContentSerializer
)


@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAuthenticated])
@catch_view_exception(('name', 'programming_language'), file_manager_logger)
def create_file(request):
    file = FileManager.create_file(request.data['name'],
                                   request.data['programming_language'],
                                   request.user,
                                   request.data.get('prev_file_id'))
    serializer = FileWithoutContentSerializer(file)
    return JsonResponse(serializer.data, status=status.HTTP_201_CREATED)


@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAuthenticated])
@catch_view_exception(['file_id'], file_manager_logger)
def delete_file(request):
    try:
        FileManager.delete_file(request.data['file_id'],
                                request.user)
        return HttpResponse(status=status.HTTP_204_NO_CONTENT)
    except FileManageException as e:
        return HttpResponse(content=e.message, status=e.response_status)


@csrf_exempt
@api_view(['GET'])
@permission_classes([IsAuthenticated])
@catch_view_exception([], file_manager_logger)
def my_files(request):
    files = FileManager.get_user_files(request.user)
    serializer = UserFilesSerializer(files, many=True)
    return JsonResponse(serializer.data, status=status.HTTP_200_OK, safe=False)


@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAuthenticated])
@catch_view_exception(['file_id'], file_manager_logger)
def open_file(request):
    try:
        file_link = FileManager.generate_link(request.data['file_id'])
        return HttpResponse(file_link, status=status.HTTP_200_OK)
    except FileManageException as e:
        return HttpResponse(content=e.message, status=e.response_status)


@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAuthenticated])
@catch_view_exception(['file_id'], file_manager_logger)
def leave_file(request):
    try:
        FileManager.leave_file(request.data['file_id'],
                               request.user)
        return HttpResponse(status=status.HTTP_204_NO_CONTENT)
    except FileManageException as e:
        return HttpResponse(content=e.message, status=e.response_status)
