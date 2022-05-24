from smtplib import SMTPException
import datetime
import traceback

from rest_framework.views import exception_handler
from django.http import HttpResponse
from rest_framework import status

from authentication.models import CustomUser
from helpers.logger import create_logger


out_logger = create_logger('custom_exception_handler_logger')


def custom_exception_handler(exc, context):
    # Call REST framework's default exception handler first,
    # to get the standard error response.
    response = exception_handler(exc, context)

    if response is None:
        if isinstance(exc, SMTPException):
            if context['request'].stream.path == '/auth/users/':
                CustomUser.objects.filter(username=context['request'].data['username'],
                                          email=context['request'].data['email']).all().delete()

            response = HttpResponse(content=str(exc),
                                    status=status.HTTP_400_BAD_REQUEST)

        else:
            out_logger.error(f"UNKNOWN EXCEPTION {__name__} {exc} {traceback.format_exc()}")
            response = HttpResponse(content=f"{str(exc)}\n problem in server, "
                                            "please report the error to 'msmorozova_3@edu.hse.ru' "
                                            "and specify the date: " + str(datetime.datetime.now()),
                                    status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return response
