"""Production monitoring and health checks."""
import time
import logging
import signal
import sys
from typing import Dict, Any, Optional
from contextlib import contextmanager

from .config import settings
from .database import check_database_health, close_database_connections

logger = logging.getLogger(__name__)

# Global shutdown flag
_shutdown_requested = False


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    global _shutdown_requested
    logger.info(f"Received signal {signum}, initiating graceful shutdown...")
    _shutdown_requested = True


def setup_signal_handlers():
    """Setup signal handlers for graceful shutdown."""
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    logger.info("Signal handlers configured")


def is_shutdown_requested() -> bool:
    """Check if shutdown has been requested."""
    return _shutdown_requested


@contextmanager
def graceful_shutdown():
    """Context manager for graceful shutdown handling."""
    setup_signal_handlers()
    try:
        yield
    finally:
        logger.info("Performing cleanup...")
        close_database_connections()
        logger.info("Cleanup completed")


def get_system_health() -> Dict[str, Any]:
    """Get comprehensive system health status."""
    health = {
        "status": "healthy",
        "timestamp": time.time(),
        "version": "1.0.0",
        "components": {}
    }
    
    # Database health
    try:
        db_health = check_database_health()
        health["components"]["database"] = db_health
        if db_health["status"] != "healthy":
            health["status"] = "degraded"
    except Exception as e:
        health["components"]["database"] = {"status": "unhealthy", "error": str(e)}
        health["status"] = "unhealthy"
    
    # Configuration health
    try:
        from .config import validate_config
        validate_config()
        health["components"]["configuration"] = {"status": "healthy"}
    except Exception as e:
        health["components"]["configuration"] = {"status": "unhealthy", "error": str(e)}
        health["status"] = "unhealthy"
    

    
    return health


def log_performance_metrics(func_name: str, duration: float, **kwargs):
    """Log performance metrics for monitoring."""
    if duration > 1.0:  # Log slow operations
        logger.warning(f"Slow operation: {func_name} took {duration:.2f}s")
    else:
        logger.debug(f"Operation: {func_name} took {duration:.2f}s")
    
    # Add any additional metrics
    for key, value in kwargs.items():
        logger.debug(f"Metric {key}: {value}")


def monitor_query_performance():
    """Decorator to monitor query performance."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                log_performance_metrics(func.__name__, duration, success=True)
                return result
            except Exception as e:
                duration = time.time() - start_time
                log_performance_metrics(func.__name__, duration, success=False, error=str(e))
                raise
        return wrapper
    return decorator
