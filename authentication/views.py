from django.http import HttpResponse
from rest_framework.decorators import api_view
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt

from authentication.backend import AuthBackend
from helpers.helper import catch_view_exception
from .auth_logger import auth_logger
from .exceptions import AuthenticationException

auth_backend = AuthBackend()


@csrf_exempt
@api_view(['POST'])
@catch_view_exception(['username'], auth_logger)
def check_username(request):
    try:
        auth_backend.is_unique_username(request.data['username'])
        return HttpResponse(status=status.HTTP_204_NO_CONTENT)
    except AuthenticationException as e:
        return HttpResponse(content=e.message, status=e.response_status)


@csrf_exempt
@api_view(['POST'])
@catch_view_exception(['email'], auth_logger)
def check_email(request):
    try:
        auth_backend.is_unique_email(request.data['email'])
        return HttpResponse(status=status.HTTP_204_NO_CONTENT)
    except AuthenticationException as e:
        return HttpResponse(content=e.message, status=e.response_status)
