from django.contrib.auth.backends import AllowAllUsersModelBackend
from django.db.utils import IntegrityError

from authentication.models import CustomUser
from .exceptions import NotUniqueFieldException, UserAlreadyExistException


class AuthBackend(AllowAllUsersModelBackend):
    @staticmethod
    def is_unique_username(username):
        if CustomUser.objects.filter(username=username).exists():
            raise NotUniqueFieldException('username')
        return True

    @staticmethod
    def is_unique_email(email):
        if CustomUser.objects.filter(email=email).exists():
            raise NotUniqueFieldException('email')
        return True

    def create_user(self, username, email, password) -> CustomUser:
        try:
            user = CustomUser.objects.create_user(username=username,
                                                  email=email,
                                                  password=password)
            return user
        except IntegrityError:
            raise UserAlreadyExistException()
