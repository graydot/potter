#!/usr/bin/env python3
"""
Custom Exception Hierarchy for Potter
Provides specific exceptions for different error scenarios
"""


class PotterException(Exception):
    """Base exception for all Potter-specific errors"""
    
    def __init__(self, message: str, details: dict = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}
    
    def __str__(self):
        if self.details:
            details_str = ", ".join(f"{k}={v}" for k, v in self.details.items())
            return f"{self.message} ({details_str})"
        return self.message


class ConfigurationException(PotterException):
    """Base exception for configuration-related errors"""
    pass


class MissingApiKeyException(ConfigurationException):
    """Raised when an API key is not configured"""
    
    def __init__(self, provider: str):
        super().__init__(
            f"{provider.title()} API key not configured",
            {"provider": provider}
        )
        self.provider = provider


class InvalidApiKeyException(ConfigurationException):
    """Raised when an API key is invalid"""
    
    def __init__(self, provider: str, reason: str = None):
        message = f"Invalid {provider.title()} API key"
        if reason:
            message += f": {reason}"
        super().__init__(message, {"provider": provider, "reason": reason})
        self.provider = provider
        self.reason = reason


class InvalidSettingsException(ConfigurationException):
    """Raised when settings are invalid or corrupted"""
    
    def __init__(self, reason: str):
        super().__init__(f"Invalid settings: {reason}", {"reason": reason})


class ProcessingException(PotterException):
    """Base exception for text processing errors"""
    pass


class ClipboardAccessException(ProcessingException):
    """Raised when clipboard access fails"""
    
    def __init__(self, operation: str, reason: str = None):
        message = f"Clipboard {operation} failed"
        if reason:
            message += f": {reason}"
        super().__init__(message, {"operation": operation, "reason": reason})
        self.operation = operation


class LLMProviderException(ProcessingException):
    """Raised when LLM provider operations fail"""
    
    def __init__(self, provider: str, operation: str, reason: str = None):
        message = f"{provider.title()} {operation} failed"
        if reason:
            message += f": {reason}"
        super().__init__(
            message, 
            {"provider": provider, "operation": operation, "reason": reason}
        )
        self.provider = provider
        self.operation = operation


class PromptNotFoundException(ProcessingException):
    """Raised when a requested prompt is not found"""
    
    def __init__(self, prompt_name: str):
        super().__init__(
            f"Prompt '{prompt_name}' not found",
            {"prompt_name": prompt_name}
        )
        self.prompt_name = prompt_name


class SystemException(PotterException):
    """Base exception for system-level errors"""
    pass


class PermissionDeniedException(SystemException):
    """Raised when system permissions are denied"""
    
    def __init__(self, permission_type: str, reason: str = None):
        message = f"{permission_type.title()} permission denied"
        if reason:
            message += f": {reason}"
        super().__init__(
            message,
            {"permission_type": permission_type, "reason": reason}
        )
        self.permission_type = permission_type


class HotkeyRegistrationException(SystemException):
    """Raised when hotkey registration fails"""
    
    def __init__(self, hotkey: str, reason: str = None):
        message = f"Failed to register hotkey '{hotkey}'"
        if reason:
            message += f": {reason}"
        super().__init__(message, {"hotkey": hotkey, "reason": reason})
        self.hotkey = hotkey


class InstanceAlreadyRunningException(SystemException):
    """Raised when another instance is already running"""
    
    def __init__(self):
        super().__init__(
            "Another instance of Potter is already running",
            {"action": "Please close the existing instance first"}
        )


class ServiceException(PotterException):
    """Base exception for service-related errors"""
    pass


class ServiceError(ServiceException):
    """Raised when service operations fail"""
    
    def __init__(self, message: str, service_name: str = None, details: str = None):
        service_details = {}
        if service_name:
            service_details["service"] = service_name
        if details:
            service_details["details"] = details
        
        super().__init__(message, service_details)
        self.service_name = service_name


class ValidationException(PotterException):
    """Raised when validation fails"""
    
    def __init__(self, message: str, field: str = None, value: str = None):
        validation_details = {}
        if field:
            validation_details["field"] = field
        if value:
            validation_details["value"] = value
        
        super().__init__(message, validation_details)
        self.field = field
        self.value = value


# User-friendly error messages mapping
USER_FRIENDLY_MESSAGES = {
    MissingApiKeyException: {
        "title": "API Key Required",
        "message": "Please configure your {provider} API key in Settings.",
        "action": "Open Settings and add your API key"
    },
    InvalidApiKeyException: {
        "title": "Invalid API Key", 
        "message": "Your {provider} API key appears to be invalid.",
        "action": "Check your API key in Settings"
    },
    ClipboardAccessException: {
        "title": "Clipboard Error",
        "message": "Unable to access clipboard.",
        "action": "Check clipboard permissions"
    },
    LLMProviderException: {
        "title": "AI Processing Error",
        "message": "Failed to process text with {provider}.",
        "action": "Try again or check your internet connection"
    },
    PromptNotFoundException: {
        "title": "Prompt Not Found",
        "message": "The selected prompt is not available.",
        "action": "Select a different prompt or add a new one"
    },
    PermissionDeniedException: {
        "title": "Permission Required",
        "message": "Potter needs {permission_type} permission to work.",
        "action": "Grant permission in System Settings"
    },
    HotkeyRegistrationException: {
        "title": "Hotkey Error",
        "message": "Failed to register the hotkey.",
        "action": "Try a different hotkey combination"
    },
    InstanceAlreadyRunningException: {
        "title": "Already Running",
        "message": "Potter is already running.",
        "action": "Close the existing instance first"
    },
    ValidationException: {
        "title": "Validation Error",
        "message": "Invalid input: {message}",
        "action": "Please correct the input and try again"
    }
}


def get_user_friendly_message(exception: PotterException) -> dict:
    """
    Get user-friendly message for an exception
    
    Args:
        exception: The Potter exception
        
    Returns:
        Dict with 'title', 'message', and 'action' keys
    """
    exc_type = type(exception)
    template = USER_FRIENDLY_MESSAGES.get(exc_type, {
        "title": "Error",
        "message": str(exception),
        "action": "Please try again"
    })
    
    # Format message with exception details
    result = {}
    for key, value in template.items():
        if isinstance(value, str) and hasattr(exception, '__dict__'):
            try:
                result[key] = value.format(**exception.__dict__)
            except (KeyError, AttributeError):
                result[key] = value
        else:
            result[key] = value
    
    return result 