from django.test import TestCase

from authentication.backend import AuthBackend
from authentication.models import CustomUser
from authentication.exceptions import UserAlreadyExistException, NotUniqueFieldException


class CreateUser(TestCase):
    def setUp(self) -> None:
        self.auth_backend = AuthBackend()

    def test_new_user(self):
        username = 'Igor Mashtakov'
        email = 'masht@mail.ru'
        password = '12345'
        self.auth_backend.create_user(username, email, password)
        user = CustomUser.objects.get(username=username, email=email)
        self.assertTrue(user.check_password(password))

    def test_user_exist(self):
        user_dict = {'username': 'Igor Mashtakov',
                     'email': 'masht@mail.ru',
                     'password': '12345'}
        self.auth_backend.create_user(**user_dict)
        with self.assertRaises(UserAlreadyExistException):
            self.auth_backend.create_user(**user_dict)

    def test_username_exist(self):
        fst_user = {'username': 'Igor Mashtakov',
                    'email': 'masht@mail.ru',
                    'password': '12345'}
        snd_user = {'username': 'Igor Mashtakov',
                    'email': 'mas@mail.ru',
                    'password': '123'}
        self.auth_backend.create_user(**fst_user)
        with self.assertRaises(UserAlreadyExistException):
            self.auth_backend.create_user(**snd_user)

    def test_email_exist(self):
        fst_user = {'username': 'Igor Mashtov',
                    'email': 'masht@mail.ru',
                    'password': '1234556'}
        snd_user = {'username': 'Igor Mashtakov',
                    'email': 'masht@mail.ru',
                    'password': '12345'}
        self.auth_backend.create_user(**fst_user)
        with self.assertRaises(UserAlreadyExistException):
            self.auth_backend.create_user(**snd_user)

    def test_username_and_email_exist(self):
        fst_user = {'username': 'Igor Mashtakov',
                    'email': 'masht@mail.ru',
                    'password': '12345'}
        snd_user = {'username': 'Igor Mashtakov',
                    'email': 'masht@mail.ru',
                    'password': '123'}
        self.auth_backend.create_user(**fst_user)
        with self.assertRaises(UserAlreadyExistException):
            self.auth_backend.create_user(**snd_user)

    def test_password_exist(self):
        fst_username, fst_email, fst_password = 'Igor Mashtakov', 'masht@mail.ru', '12345'
        snd_username, snd_email, snd_password = 'Igor Mashtov', 'mas@mail.ru', '12345'

        self.auth_backend.create_user(fst_username, fst_email, fst_password)
        fst_user = CustomUser.objects.get(username=fst_username, email=fst_email)
        self.assertTrue(fst_user.check_password(fst_password))

        self.auth_backend.create_user(snd_username, snd_email, snd_password)
        snd_user = CustomUser.objects.get(username=snd_username, email=snd_email)
        self.assertTrue(snd_user.check_password(snd_password))


class CheckUsername(TestCase):
    def setUp(self) -> None:
        self.auth_backend = AuthBackend()

    def test_username_is_correct(self):
        username = 'Igor Mashtakov'
        self.assertTrue(self.auth_backend.is_unique_username(username))

    def test_username_already_exist(self):
        username = 'Igor Mashtakov'
        email = 'masht@mail.ru'
        password = '12345'
        self.auth_backend.create_user(username, email, password)
        with self.assertRaises(NotUniqueFieldException):
            self.auth_backend.is_unique_username(username)


class CheckEmail(TestCase):

    def setUp(self) -> None:
        self.auth_backend = AuthBackend()

    def test_email_is_correct(self):
        email = 'masht@mail.ru'
        self.assertTrue(self.auth_backend.is_unique_email(email))

    def test_email_already_exist(self):
        username = 'Igor Mashtakov'
        email = 'masht@mail.ru'
        password = '12345'
        self.auth_backend.create_user(username, email, password)
        with self.assertRaises(NotUniqueFieldException):
            self.auth_backend.is_unique_email(email)
