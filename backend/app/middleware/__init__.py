"""
Middleware module
Eksportuje funkcje setup dla error handling i logging middleware.
"""

from app.middleware.error_handler import setup_exception_handlers
from app.middleware.logging import setup_logging_middleware

__all__ = [
    "setup_exception_handlers",
    "setup_logging_middleware"
]
