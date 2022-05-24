from .exceptions import FileAlreadyRunningException, FileNotRunningException


class SingletonMeta(type):

    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]


class LaunchedFilesManager(metaclass=SingletonMeta):
    def __init__(self):
        self.launched_files = {}

    def add_running_file(self, file_id, thread):
        if self.file_is_running(file_id):
            raise FileAlreadyRunningException(file_id)
        else:
            self.launched_files[file_id] = thread

    def file_is_running(self, file_id):
        return file_id in self.launched_files

    def remove_stopped_file(self, file_id):
        del self.launched_files[file_id]

    def get_thread_by_file_id(self, file_id):
        try:
            return self.launched_files[file_id]
        except KeyError:
            raise FileNotRunningException(file_id)
