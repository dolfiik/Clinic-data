"""
Global Error Handler Middleware
Obsługuje wszystkie błędy w aplikacji i zwraca spójne JSON responses.
"""

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import traceback
import logging

logger = logging.getLogger(__name__)

async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """
    Handler dla HTTPException
    
    Zwraca spójny format błędu:
    {
        "error": "Error Type",
        "detail": "Error message",
        "path": "/api/v1/endpoint"
    }
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail if isinstance(exc.detail, str) else "Error",
            "detail": exc.detail,
            "path": str(request.url.path)
        }
    )

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handler dla błędów walidacji Pydantic
    
    Formatuje błędy walidacji w czytelny sposób
    """
    errors = []
    for error in exc.errors():
        field = " -> ".join(str(loc) for loc in error["loc"])
        errors.append({
            "field": field,
            "message": error["msg"],
            "type": error["type"]
        })
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation Error",
            "detail": "Request validation failed",
            "path": str(request.url.path),
            "errors": errors
        }
    )

async def internal_exception_handler(request: Request, exc: Exception):
    """
    Handler dla nieoczekiwanych błędów (500)
    
    Loguje pełny traceback i zwraca ogólny komunikat użytkownikowi
    """
    # Log pełnego tracebacku dla debugowania
    logger.error(f"Internal server error on {request.method} {request.url.path}")
    logger.error(f"Exception: {type(exc).__name__}: {str(exc)}")
    logger.error(traceback.format_exc())
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "detail": "An unexpected error occurred. Please contact support if the problem persists.",
            "path": str(request.url.path)
        }
    )

def setup_exception_handlers(app):
    """
    Rejestruje wszystkie exception handlers w aplikacji FastAPI
    
    Użycie w main.py:
        from app.middleware.error_handler import setup_exception_handlers
        setup_exception_handlers(app)
    """
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, internal_exception_handler)
