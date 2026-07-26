"""
AI Service Exceptions
====================
Custom exceptions for the AI Integration Layer.
"""

class AIServiceException(Exception):
    """Base exception for AI Integration Layer."""
    pass

class AIValidationError(AIServiceException):
    """Raised when request payload or response structure validation fails."""
    pass

class AIConnectionError(AIServiceException):
    """Raised when network connection to AI engine fails."""
    pass

class AITimeoutError(AIServiceException):
    """Raised when call to AI engine times out."""
    pass

class AIUnavailableError(AIServiceException):
    """Raised when AI engine is unavailable/unhealthy."""
    pass
