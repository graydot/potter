#!/usr/bin/env python3
"""
Sentry Client - Handles Sentry integration with silent no-ops when disabled
"""

import os
import sys
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class SentryClient:
    """Sentry client that does silent no-ops when not enabled"""
    
    def __init__(self, environment: str, build_info: Dict[str, Any]):
        self.enabled = False
        self.environment = environment
        self.build_info = build_info
        self._setup()
    
    def _setup(self):
        """Setup Sentry if available and configured"""
        try:
            # Check if DSN is configured
            dsn = os.getenv('SENTRY_DSN', 'YOUR_SENTRY_DSN_HERE')
            if not dsn or dsn == 'YOUR_SENTRY_DSN_HERE':
                logger.debug("Sentry DSN not configured, running in no-op mode")
                return
            
            import sentry_sdk
            from sentry_sdk.integrations.logging import LoggingIntegration
            
            # Configure Sentry with free tier considerations
            sentry_logging = LoggingIntegration(
                level=logging.WARNING,
                event_level=logging.ERROR
            )
            
            sentry_sdk.init(
                dsn=dsn,
                environment=self.environment,
                release=f"potter@{self.build_info.get('version', 'unknown')}",
                integrations=[sentry_logging],
                traces_sample_rate=0.0,
                profiles_sample_rate=0.0,
                max_breadcrumbs=10,
                attach_stacktrace=True,
                sample_rate=self._get_sample_rate(),
            )
            
            # Set contexts
            sentry_sdk.set_context("build", {
                "build_id": self.build_info.get("build_id"),
                "version": self.build_info.get("version"),
                "timestamp": self.build_info.get("timestamp"),
                "environment": self.environment
            })
            
            import platform
            sentry_sdk.set_context("system", {
                "platform": platform.system(),
                "platform_version": platform.release(),
                "python_version": platform.python_version(),
                "frozen": getattr(sys, 'frozen', False)
            })
            
            self.enabled = True
            logger.info(f"✅ Sentry initialized for environment: {self.environment}")
            
        except ImportError:
            logger.debug("Sentry SDK not available")
        except Exception as e:
            logger.warning(f"Failed to initialize Sentry: {e}")
    
    def _get_sample_rate(self) -> float:
        """Get sample rate based on environment"""
        rates = {
            "development": 1.0,
            "build_script": 1.0,
            "release": 1.0,
            "appstore": 1.0,
            "unknown": 0.5
        }
        return rates.get(self.environment, 1.0)
    
    def capture_exception(self, exception: Exception, 
                          context: Optional[Dict[str, Any]] = None, 
                          extra_info: Optional[str] = None):
        """Capture exception to Sentry (no-op if not enabled)"""
        if not self.enabled:
            return
        
        try:
            import sentry_sdk
            with sentry_sdk.push_scope() as scope:
                if context:
                    for key, value in context.items():
                        scope.set_extra(key, value)
                
                if extra_info:
                    scope.set_extra("additional_info", extra_info)
                
                sentry_sdk.capture_exception(exception)
        except Exception:
            pass  # Silent failure for Sentry issues
    
    def capture_message(self, message: str, level: str = "error", context: Optional[Dict[str, Any]] = None):
        """Capture message to Sentry (no-op if not enabled)"""
        if not self.enabled:
            return
        
        try:
            import sentry_sdk
            with sentry_sdk.push_scope() as scope:
                if context:
                    for key, value in context.items():
                        scope.set_extra(key, value)
                
                sentry_sdk.capture_message(message, level=level)
        except Exception:
            pass  # Silent failure for Sentry issues


# Global instance
_sentry_client = None


def get_sentry_client() -> SentryClient:
    """Get the global Sentry client instance"""
    global _sentry_client
    if _sentry_client is None:
        # Import here to avoid circular imports
        from utils.instance_checker import load_build_id
        
        # Detect environment
        environment = "development"
        if getattr(sys, 'frozen', False):
            environment = "release"
        elif 'build_app.py' in sys.argv[0]:
            environment = "build_script"
        
        # Load build info
        try:
            build_info = load_build_id()
        except Exception:
            build_info = {"build_id": "unknown", "version": "unknown", "timestamp": "unknown"}
        
        _sentry_client = SentryClient(environment, build_info)
    
    return _sentry_client 