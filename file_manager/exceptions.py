from rest_framework import status


class FileManageException(Exception):
    def __init__(self, message, response_status):
        self.message = message
        self.response_status = response_status


class NoRequiredFileAccess(FileManageException):
    def __init__(self, required_access):
        super().__init__(f"You must be {required_access} that to do this", status.HTTP_406_NOT_ACCEPTABLE)


class FileDoesNotExistException(FileManageException):
    def __init__(self):
        super().__init__("Such file does not exist", status.HTTP_404_NOT_FOUND)


class UnableToDecodeFileException(FileManageException):
    def __init__(self):
        super().__init__("Unable to decode file", status.HTTP_400_BAD_REQUEST)


class FileAlreadyRunningException(FileManageException):
    def __init__(self, file):
        super().__init__(f"The file {file} is already running", status.HTTP_409_CONFLICT)


class FileNotRunningException(FileManageException):
    def __init__(self, file):
        super().__init__(f"The file {file} is not running", status.HTTP_409_CONFLICT)
