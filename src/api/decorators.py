from functools import wraps

from rest_framework import status
from rest_framework.response import Response


def validate(serializer, partial=False):
    def wrapper(f):
        @wraps(f)
        def wrapped(self, request, *args, **kwargs):
            instance = serializer(data=request.data, partial=partial, context={'request': request})
            instance.is_valid(raise_exception=True)
            return f(self, request, *args, data=instance.validated_data, serializer=instance, **kwargs)

        return wrapped

    return wrapper


def wrap_response(serializer=None):
    def wrapper(f):
        @wraps(f)
        def wrapped(self, request, *args, **kwargs):
            data = f(self, request, *args, **kwargs)
            if isinstance(data, Response):
                return data
            elif serializer is not None:
                instance = serializer(data, context={'request': request})
                return Response(instance.data)
            elif data is None:
                return Response(status=status.HTTP_204_NO_CONTENT)
            else:
                return Response(data)

        return wrapped

    return wrapper
