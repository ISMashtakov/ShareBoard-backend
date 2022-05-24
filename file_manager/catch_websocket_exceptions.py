import traceback

from rest_framework import status

from .logger import file_manager_logger


def catch_websocket_exception(required_request_fields):
    def decorator(func):
        def wrap(self, event, *args, **kwargs):
            # check necessary fields in package
            for field in required_request_fields:
                try:
                    event[field]
                except KeyError:
                    message = f"{field} is empty field"
                    file_manager_logger.error(message)
                    self.send_json({'type': event['type'],
                                    'error_code': 4000 + status.HTTP_404_NOT_FOUND,
                                    'message': f"{message} in {event}"}, close=True)

            # catch unknown exceptions
            try:
                return func(self, event, *args, **kwargs)
            except Exception as e:
                file_manager_logger.error(f"UNKNOWN EXCEPTION {__name__} {e} {traceback.format_exc()}")
                self.close(4500)
        return wrap
    return decorator
