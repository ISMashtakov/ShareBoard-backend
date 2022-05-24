from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser, BaseUserManager
)
from django.db.models import Q
from django.utils import timezone

from .account_colors import random_color


class CustomAccountManager(BaseUserManager):
    """
    Creates and saves a User with the given email,and password.
    """

    def create_user(self, username, email, password):
        """
        Creates and saves a User with the given username,and password.
        """
        user = self.model(username=username,
                          email=email,
                          account_color=random_color())
        user.set_password(password)
        user.save(using=self._db)
        return user

    def get_by_natural_key(self, username):
        return self.get(
            Q(**{self.model.USERNAME_FIELD: username}) |
            Q(**{self.model.EMAIL_FIELD: username})
        )


class CustomUser(AbstractBaseUser):
    """
    An abstract base class implementing a fully featured User model.

    """
    username = models.CharField(unique=True, max_length=200)
    email = models.EmailField(unique=True)
    account_color = models.CharField(max_length=7)
    is_active = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    last_login = None

    objects = CustomAccountManager()

    USERNAME_FIELD = 'username'
    EMAIL_FIELD = 'email'

    REQUIRED_FIELDS = []

    def save(self, *args, **kwargs):
        super(CustomUser, self).save(*args, **kwargs)
        return self
