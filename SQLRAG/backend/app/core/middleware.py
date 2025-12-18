"""Production-ready middleware for request tracking, logging, and error handling."""
import logging
import time
import uuid
from typing import Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging_config import request_id_var, get_logger
from app.core.exceptions import SQLRAGException
from app.db.session import engine

logger = get_logger(__name__)



class RequestIdMiddleware(BaseHTTPMiddleware):
    """Middleware to add unique request IDs for distributed tracing."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate or extract request ID
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        
        # Store in context variable for logging
        request_id_var.set(request_id)
        
        # Process request
        response = await call_next(request)
        
        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id
        
        return response


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log all requests and responses with timing."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.perf_counter()
        
        user = getattr(request.state, "user", None)
        user_id = getattr(user, "id", None)
        role = getattr(user, "role", None)

        # Log incoming request
        logger.info(
            f"Request: {request.method} {request.url.path}",
            extra={"extra_data": {
                "method": request.method,
                "path": request.url.path,
                "query": str(request.query_params),
                "client_ip": request.client.host if request.client else None,
                "user_id": user_id,
                "role": role,
            }}
        )
        
        try:
            response = await call_next(request)
            
            # Calculate duration
            duration_ms = (time.perf_counter() - start_time) * 1000
            
            # Log response with pool info
            log_level = logging.WARNING if response.status_code >= 400 else logging.INFO
            pool_info = "n/a"
            if hasattr(engine.pool, "status"):
                pool_info = engine.pool.status()

            logger.log(
                log_level,
                f"Response: {response.status_code} ({duration_ms:.2f}ms)",
                extra={"extra_data": {
                    "status_code": response.status_code,
                    "duration_ms": round(duration_ms, 2),
                    "path": request.url.path,
                    "user_id": user_id,
                    "role": role,
                    "db_pool": pool_info
                }}
            )

            
            return response
            
        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.error(
                f"Request failed: {str(e)} ({duration_ms:.2f}ms)",
                exc_info=True,
                extra={"extra_data": {
                    "duration_ms": round(duration_ms, 2),
                    "path": request.url.path,
                }}
            )
            raise


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Global exception handler for unhandled errors."""
    request_id = request_id_var.get()
    
    if isinstance(exc, SQLRAGException):
        # Known application exception
        logger.warning(
            f"Application error: {exc.message}",
            extra={"extra_data": exc.details}
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                **exc.to_dict(),
                "request_id": request_id,
            }
        )
    
    # Unknown exception - log full details
    logger.error(
        f"Unhandled exception: {str(exc)}",
        exc_info=True,
        extra={"extra_data": {"path": request.url.path}}
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "InternalServerError",
            "message": "An unexpected error occurred. Please try again later.",
            "request_id": request_id,
        }
    )
