#!/usr/bin/env python3
"""
Exception Reporter - Centralized error handling and reporting
Simple, clean exception reporting with optional Sentry integration
"""

import logging
import traceback
from typing import Optional, Dict, Any
from functools import wraps

logger = logging.getLogger(__name__)


class ExceptionReporter:
    """Simple exception reporter with optional Sentry integration"""
    
    def __init__(self):
        self.sentry_client = None
        try:
            from utils.sentry_client import get_sentry_client
            self.sentry_client = get_sentry_client()
        except ImportError:
            logger.debug("Sentry client not available")
    
    def _avoid_clipboard_content(self, text: str) -> str:
        """Simple check to avoid logging clipboard content"""
        if isinstance(text, str) and len(text) > 100:
            # If it's a long string, it might be clipboard content
            return "[CONTENT_REDACTED]"
        return text
    
    def _clean_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Remove potential clipboard content from context"""
        if not context:
            return {}
        
        cleaned = {}
        for key, value in context.items():
            if isinstance(value, str):
                cleaned[key] = self._avoid_clipboard_content(value)
            else:
                cleaned[key] = value
        return cleaned
    
    def report_exception(self, exception: Exception, 
                        context: Optional[Dict[str, Any]] = None,
                        level: str = "error",
                        extra_info: Optional[str] = None) -> str:
        """Report an exception with full context"""
        try:
            # Create error message
            error_msg = f"{type(exception).__name__}: {str(exception)}"
            if extra_info:
                error_msg = f"{extra_info} - {error_msg}"
            
            # Clean context to avoid clipboard content
            safe_context = self._clean_context(context)
            
            # Log locally
            log_level = getattr(logging, level.upper(), logging.ERROR)
            logger.log(log_level, f"Exception reported: {error_msg}")
            if safe_context:
                logger.log(log_level, f"Context: {safe_context}")
            logger.log(log_level, f"Traceback:\n{traceback.format_exc()}")
            
            # Send to Sentry if available
            if self.sentry_client:
                self.sentry_client.capture_exception(exception, safe_context, extra_info)
            
            return error_msg
            
        except Exception as report_error:
            # Fallback logging if reporting itself fails
            fallback_msg = f"Exception reporting failed: {report_error}"
            logger.error(fallback_msg)
            return f"Failed to report exception: {exception}"
    
    def report_error(self, message: str, context: Optional[Dict[str, Any]] = None):
        """Report a non-exception error"""
        try:
            safe_context = self._clean_context(context)
            safe_message = self._avoid_clipboard_content(message)
            
            logger.error(f"Error reported: {safe_message}")
            if safe_context:
                logger.error(f"Context: {safe_context}")
            
            if self.sentry_client:
                self.sentry_client.capture_message(safe_message, level='error', context=safe_context)
        
        except Exception as e:
            logger.error(f"Failed to report error: {e}")
    
    def report_warning(self, message: str, context: Optional[Dict[str, Any]] = None):
        """Report a warning"""
        try:
            safe_context = self._clean_context(context)
            safe_message = self._avoid_clipboard_content(message)
            
            logger.warning(f"Warning reported: {safe_message}")
            if safe_context:
                logger.warning(f"Context: {safe_context}")
            
            if self.sentry_client:
                self.sentry_client.capture_message(safe_message, level='warning', context=safe_context)
        
        except Exception as e:
            logger.warning(f"Failed to report warning: {e}")
    
    def safe_execute(self, func, *args, **kwargs):
        """Execute a function safely with automatic exception reporting"""
        try:
            return func(*args, **kwargs)
        except Exception as e:
            context = {
                "function": func.__name__ if hasattr(func, '__name__') else str(func),
                "args_count": len(args),
                "kwargs_keys": list(kwargs.keys()) if kwargs else []
            }
            self.report_exception(e, context, extra_info=f"Safe execution of {func}")
            return None


# Global instance
_exception_reporter = None


def get_exception_reporter() -> ExceptionReporter:
    """Get the global exception reporter instance"""
    global _exception_reporter
    if _exception_reporter is None:
        _exception_reporter = ExceptionReporter()
    return _exception_reporter


def report_exception(exception: Exception, 
                    context: Optional[Dict[str, Any]] = None,
                    level: str = "error",
                    extra_info: Optional[str] = None) -> str:
    """Global function to report exceptions"""
    return get_exception_reporter().report_exception(exception, context, level, extra_info)


def report_error(message: str, context: Optional[Dict[str, Any]] = None):
    """Global function to report errors"""
    get_exception_reporter().report_error(message, context)


def report_warning(message: str, context: Optional[Dict[str, Any]] = None):
    """Global function to report warnings"""
    get_exception_reporter().report_warning(message, context)


def safe_execute(func, *args, **kwargs):
    """Global function for safe execution"""
    return get_exception_reporter().safe_execute(func, *args, **kwargs)


def exception_handler(func):
    """Decorator for automatic exception handling"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            context = {
                "function": func.__name__,
                "module": func.__module__,
                "args_count": len(args),
                "kwargs_keys": list(kwargs.keys()) if kwargs else []
            }
            report_exception(e, context, extra_info=f"Exception in {func.__name__}")
            return None
    return wrapper 