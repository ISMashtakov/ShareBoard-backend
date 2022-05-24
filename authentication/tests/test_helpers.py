from django.http import HttpResponse
from django.test import TestCase, RequestFactory
from rest_framework.decorators import api_view
from rest_framework import status

from helpers.helper import catch_view_exception


class TestLogger:
    def error(self, error):
        pass


test_logger = TestLogger()


@api_view(['POST'])
@catch_view_exception(('username', 'email'), test_logger)
def test_view(request):
    if not request.data['username']:
        raise Exception()
    return HttpResponse(status=status.HTTP_200_OK)


class HelperTests(TestCase):
    def setUp(self) -> None:
        self.factory = RequestFactory()

    def test_bad_type_request_put(self):
        request = self.factory.put('/tests/helper')
        response = test_view(request)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(str(response.data['detail']), 'Method "PUT" not allowed.')

    def test_no_username_in_params(self):
        request = self.factory.post('/tests/helper', {'email': 'masht@mail.ru'})
        response = test_view(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.content, b'username not given')

    def test_unnecessary_param(self):
        request = self.factory.post('/tests/helper', {'username': 'Igor',
                                                      'email': 'masht@mail.ru',
                                                      'password': '12345'})
        response = test_view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_another_exception(self):
        request = self.factory.post('/tests/helper', {'username': '',
                                                      'email': 'masht@mail.ru'})
        response = test_view(request)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertTrue(b'problem in server' in response.content)

    def test_ok(self):
        request = self.factory.post('/tests/helper', {'username': 'Igor',
                                                      'email': 'masht@mail.ru'})
        response = test_view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
