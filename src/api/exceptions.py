import logging

from django.core.exceptions import PermissionDenied
from django.http import Http404
from rest_framework import exceptions
from rest_framework.exceptions import ValidationError, ErrorDetail, APIException
from rest_framework.response import Response
from rest_framework.views import set_rollback

logger = logging.getLogger(__name__)


def exception_handler(exc, context):
    if isinstance(exc, Http404):
        exc = exceptions.NotFound()
    elif isinstance(exc, PermissionDenied):
        exc = exceptions.PermissionDenied()

    if isinstance(exc, exceptions.APIException):
        headers = {}
        if hasattr(exc, 'auth_header') and exc.auth_header:
            headers['WWW-Authenticate'] = exc.auth_header
        if hasattr(exc, 'wait') and exc.wait:
            headers['Retry-After'] = '%d' % exc.wait

        data = {}
        if isinstance(exc, ValidationError):
            if isinstance(exc.detail, dict):
                data['fields'] = handle_error(exc.detail)
            else:
                data['message'] = handle_error(exc.detail)
        elif isinstance(exc.detail, (list, tuple, dict)):
            data['message'] = handle_error(exc.detail)
        else:
            data = {'message': exc.detail}
        set_rollback()
        return Response(data, status=exc.status_code, headers=headers)

    return None


def handle_error(err) -> str or dict:
    if isinstance(err, str):
        return err
    elif isinstance(err, dict):
        return {sub_field: handle_error(sub_err) for sub_field, sub_err in err.items()}
    elif isinstance(err, (list, tuple)):
        if not len(err):
            return None
        if isinstance(err[0], ErrorDetail):
            return str(err[0])
        else:
            return [handle_error(el) for el in err]
    else:
        raise APIException('Cannot handle exception')
