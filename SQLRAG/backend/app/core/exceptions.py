"""Custom exception classes for consistent error handling across the application."""
import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


class SQLRAGException(Exception):
    """Base exception for all SQLRAG application errors."""
    
    def __init__(
        self, 
        message: str, 
        details: Optional[dict[str, Any]] = None,
        status_code: int = 500
    ):
        self.message = message
        self.details = details or {}
        self.status_code = status_code
        super().__init__(self.message)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert exception to dictionary for API responses."""
        return {
            "error": self.__class__.__name__,
            "message": self.message,
            "details": self.details
        }


class DatabaseError(SQLRAGException):
    """Raised when database operations fail."""
    
    def __init__(self, message: str, details: Optional[dict[str, Any]] = None):
        super().__init__(message, details, status_code=503)


class LLMError(SQLRAGException):
    """Raised when LLM/Azure OpenAI operations fail."""
    
    def __init__(self, message: str, details: Optional[dict[str, Any]] = None):
        super().__init__(message, details, status_code=502)


class ValidationError(SQLRAGException):
    """Raised when input validation fails."""
    
    def __init__(self, message: str, details: Optional[dict[str, Any]] = None):
        super().__init__(message, details, status_code=400)


class AuthorizationError(SQLRAGException):
    """Raised when user lacks required permissions."""
    
    def __init__(self, message: str, details: Optional[dict[str, Any]] = None):
        super().__init__(message, details, status_code=403)


class ConfigurationError(SQLRAGException):
    """Raised when required configuration is missing or invalid."""
    
    def __init__(self, message: str, details: Optional[dict[str, Any]] = None):
        super().__init__(message, details, status_code=500)
