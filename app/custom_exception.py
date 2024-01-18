from django.core.exceptions import ValidationError as DjangoCoreValidationError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler
from typing import Any, Union
from rest_framework import status



class QuerySetException(Exception):
    errors: list[str]
    message: str

    def __init__(self, errors: list[str], message: str):
        self.errors = errors
        self.message = message




class CustomException(Exception):
    def __init__(
        self,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        message: Union[int, str] = None,
        errors: Any = None,
    ):
        self.status_code = status_code
        self.message = message
        self.errors = errors

def custom_exception_handler(exc, context):
    # Call REST framework's default exception handler first,
    # to get the standard error response.

    response = exception_handler(exc, context)
    if response is not None:
        response.data = {
            "status": response.status_code,
            "message": response.data,
        }

    if isinstance(exc, CustomException):
        response = Response(
            {"status": exc.status_code, "message": exc.message, "errors": exc.errors},
            status=exc.status_code,
        )
    elif isinstance(exc, QuerySetException):
        response = Response(
            {
                "status": status.HTTP_400_BAD_REQUEST,
                "message": exc.message,
                "errors": exc.errors,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )
    elif isinstance(exc, DjangoCoreValidationError):
        response = Response(
            {
                "status": status.HTTP_400_BAD_REQUEST,
                "message": exc.message,
                "errors": exc.error_list,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )
    return response