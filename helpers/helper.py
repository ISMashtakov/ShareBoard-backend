from django.http import HttpResponseBadRequest


def catch_view_exception(required_request_fields: tuple or list, logger):
    def decorator(func):
        def wrap(request):

            # check necessary fields in request
            for field in required_request_fields:
                try:
                    request.data[field]
                except KeyError:
                    logger.error(f"{field} is empty field")
                    return HttpResponseBadRequest(f"{field} not given")

            return func(request)
        return wrap
    return decorator
