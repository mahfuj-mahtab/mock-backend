from rest_framework import status
from rest_framework.exceptions import APIException, ValidationError
from rest_framework.views import exception_handler

from apps.common.responses import api_response


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is None:
        return api_response(
            success=False,
            message="Internal server error",
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    if isinstance(exc, ValidationError):
        errors = response.data
        if isinstance(errors, list):
            errors = {"non_field_errors": errors}
        return api_response(
            success=False,
            message="Validation failed",
            errors=errors,
            status=response.status_code,
        )

    if isinstance(exc, APIException):
        detail = exc.detail
        if isinstance(detail, list):
            message = detail[0] if detail else str(exc)
            errors = {"non_field_errors": detail}
        elif isinstance(detail, dict):
            message = "Validation failed" if response.status_code == 400 else str(exc)
            errors = detail
        else:
            message = str(detail)
            errors = None

        return api_response(
            success=False,
            message=message,
            errors=errors,
            status=response.status_code,
        )

    return response
