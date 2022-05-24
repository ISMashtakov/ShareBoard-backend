from rest_framework import status


class BoardManagerException(Exception):
    def __init__(self, message, response_status):
        self.message = message
        self.response_status = response_status


class NoRequiredBoardAccess(BoardManagerException):
    def __init__(self, required_access):
        super().__init__(f"You must be {required_access} that to do this", status.HTTP_406_NOT_ACCEPTABLE)


class BoardDoesNotExistException(BoardManagerException):
    def __init__(self):
        super().__init__("Such board does not exist", status.HTTP_404_NOT_FOUND)


class UnableToDecodeBoardException(BoardManagerException):
    def __init__(self):
        super().__init__("Unable to decode board", status.HTTP_400_BAD_REQUEST)


class BoardAlreadyRunningException(BoardManagerException):
    def __init__(self, board):
        super().__init__(f"The board {board} is already running", status.HTTP_409_CONFLICT)


class BoardNotRunningException(BoardManagerException):
    def __init__(self, board):
        super().__init__(f"The board {board} is not running", status.HTTP_409_CONFLICT)
