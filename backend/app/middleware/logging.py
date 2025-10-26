"""
Request/Response Logging Middleware
Loguje każdy request i response z podstawowymi metrykami.
"""

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import time
import logging
import uuid

logger = logging.getLogger(__name__)

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware logujący requesty i responses
    
    Loguje:
    - Method, path, query params
    - Request ID (UUID)
    - User ID (jeśli zalogowany)
    - Status code
    - Processing time
    - IP address
    """
    
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        start_time = time.time()
        
        method = request.method
        path = request.url.path
        query_params = str(request.url.query) if request.url.query else ""
        client_ip = request.client.host if request.client else "unknown"
        
        logger.info(
            f"[{request_id}] {method} {path} "
            f"{f'?{query_params}' if query_params else ''} "
            f"from {client_ip}"
        )
        
        try:
            response = await call_next(request)
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(
                f"[{request_id}] {method} {path} - "
                f"ERROR: {type(e).__name__}: {str(e)} "
                f"({processing_time*1000:.2f}ms)"
            )
            raise
        
        processing_time = time.time() - start_time
        
        response.headers["X-Request-ID"] = request_id
        
        status_code = response.status_code
        log_level = logging.INFO if status_code < 400 else logging.WARNING
        
        logger.log(
            log_level,
            f"[{request_id}] {method} {path} - "
            f"Status: {status_code} "
            f"({processing_time*1000:.2f}ms)"
        )
        
        return response

def setup_logging_middleware(app):
    """
    Dodaje logging middleware do aplikacji
    
    Użycie w main.py:
        from app.middleware.logging import setup_logging_middleware
        setup_logging_middleware(app)
    """
    app.add_middleware(RequestLoggingMiddleware)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
