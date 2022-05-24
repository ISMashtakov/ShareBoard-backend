from rest_framework import status


class AuthenticationException(Exception):
    def __init__(self, message, response_status):
        self.message = message
        self.response_status = response_status


class BadRequestTypeException(AuthenticationException):
    def __init__(self):
        super().__init__("Bad request type", status.HTTP_405_METHOD_NOT_ALLOWED)


class FieldNotGivenException(AuthenticationException):
    def __init__(self, field_name):
        super().__init__(f"{field_name} not given", status.HTTP_400_BAD_REQUEST)


class IllegalFieldException(AuthenticationException):
    def __init__(self, field_name):
        super().__init__(f"{field_name} is incorrect", status.HTTP_406_NOT_ACCEPTABLE)


class NotUniqueFieldException(AuthenticationException):
    def __init__(self, field_name):
        super().__init__(f"This {field_name} is already in use", status.HTTP_409_CONFLICT)


class UserDoesNotExistException(AuthenticationException):
    def __init__(self):
        super().__init__("User does not exist", status.HTTP_404_NOT_FOUND)


class UserAlreadyExistException(AuthenticationException):
    def __init__(self):
        super().__init__("This user already exist", status.HTTP_409_CONFLICT)
