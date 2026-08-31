import logging
from typing import Any, Optional
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

logger = logging.getLogger("moneybeing.exceptions")


class AppException(Exception):
    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        errors: Optional[Any] = None,
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.errors = errors


class DuplicateEntityException(AppException):
    def __init__(self, message: str = "Resource already exists", errors: Optional[Any] = None):
        super().__init__(message=message, status_code=status.HTTP_409_CONFLICT, errors=errors)


class EntityNotFoundException(AppException):
    def __init__(self, message: str = "Requested resource not found", errors: Optional[Any] = None):
        super().__init__(message=message, status_code=status.HTTP_404_NOT_FOUND, errors=errors)


# Convenient alias
NotFoundException = EntityNotFoundException


class ValidationException(AppException):
    def __init__(self, message: str = "Invalid input data", errors: Optional[Any] = None):
        super().__init__(message=message, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, errors=errors)


class AuthenticationException(AppException):
    def __init__(self, message: str = "Invalid credentials or token", errors: Optional[Any] = None):
        super().__init__(message=message, status_code=status.HTTP_401_UNAUTHORIZED, errors=errors)


class AuthorizationException(AppException):
    def __init__(self, message: str = "Insufficient permissions to perform this action", errors: Optional[Any] = None):
        super().__init__(message=message, status_code=status.HTTP_403_FORBIDDEN, errors=errors)


class ProviderException(AppException):
    def __init__(self, message: str = "Third-party service provider error", errors: Optional[Any] = None):
        super().__init__(message=message, status_code=status.HTTP_502_BAD_GATEWAY, errors=errors)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        logger.warning(f"AppException on {request.method} {request.url.path}: {exc.message}")
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "status": "error",
                "message": exc.message,
                "errors": exc.errors,
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        logger.warning(f"Validation error on {request.method} {request.url.path}: {exc.errors()}")
        formatted_errors = []
        error_details = []
        for err in exc.errors():
            raw_loc = err.get("loc", [])
            # Skip 'body' in field path for cleaner display
            field_parts = [str(l) for l in raw_loc if str(l) != "body"]
            field_name = " -> ".join(field_parts) if field_parts else "request"
            msg = err.get("msg", "Invalid value")
            formatted_errors.append({"field": field_name, "message": msg})
            error_details.append(f"{field_name}: {msg}")

        summary_msg = "Validation Error: " + "; ".join(error_details) if error_details else "Validation failed on input parameters"
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "status": "error",
                "message": summary_msg,
                "errors": formatted_errors,
            },
        )

    @app.exception_handler(IntegrityError)
    async def integrity_error_handler(request: Request, exc: IntegrityError):
        logger.error(f"Database IntegrityError on {request.method} {request.url.path}: {str(exc.orig)}")
        orig_msg = str(exc.orig).lower()
        if "mobile" in orig_msg or "unique" in orig_msg:
            return JSONResponse(
                status_code=status.HTTP_409_CONFLICT,
                content={
                    "status": "error",
                    "message": "A loan application already exists with this mobile number.",
                },
            )
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "status": "error",
                "message": "Database constraint violation occurred",
            },
        )

    @app.exception_handler(SQLAlchemyError)
    async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
        logger.error(f"Database error on {request.method} {request.url.path}: {str(exc)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "status": "error",
                "message": f"Database processing error: {str(exc.__class__.__name__)}",
            },
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.exception(f"Unhandled exception on {request.method} {request.url.path}: {str(exc)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "status": "error",
                "message": str(exc) if str(exc) else "An unexpected internal server error occurred",
            },
        )
