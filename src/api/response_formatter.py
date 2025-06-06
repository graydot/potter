#!/usr/bin/env python3
"""
Response Formatter
Consistent response formatting for API Gateway
"""

import json
import logging
from typing import Any, Dict, Optional
from datetime import datetime

from .request_handler import APIResponse, HTTPStatus

logger = logging.getLogger(__name__)


class ResponseFormatter:
    """
    Formats API responses into consistent structures
    
    Features:
    - Standardized response format
    - Multiple output formats (JSON, XML, etc.)
    - Error response formatting
    - Metadata injection
    - Content negotiation
    """
    
    def __init__(self):
        self.logger = logging.getLogger("api.response_formatter")
        self.default_format = "json"
        self.formatters = {
            'json': self._format_json,
            'xml': self._format_xml,
            'text': self._format_text
        }
    
    def format_response(self, response: APIResponse, format_type: str = None) -> Dict[str, Any]:
        """
        Format API response into specified format
        
        Args:
            response: APIResponse object
            format_type: Output format ('json', 'xml', 'text')
            
        Returns:
            Formatted response dictionary
        """
        format_type = format_type or self.default_format
        formatter = self.formatters.get(format_type, self._format_json)
        
        try:
            return formatter(response)
        except Exception as e:
            self.logger.error(f"Error formatting response: {e}")
            # Return basic error response if formatting fails
            return self._format_error_fallback(response, str(e))
    
    def _format_json(self, response: APIResponse) -> Dict[str, Any]:
        """Format response as JSON structure"""
        result = {
            'success': response.is_success(),
            'status': response.status.value,
            'timestamp': datetime.fromtimestamp(response.timestamp).isoformat(),
        }
        
        # Add data if present
        if response.data is not None:
            result['data'] = self._serialize_data(response.data)
        
        # Add error information if present
        if response.error:
            result['error'] = {
                'message': response.error,
                'code': response.error_code,
                'details': response.error_details
            }
        
        # Add metadata
        if response.metadata:
            result['metadata'] = response.metadata
        
        # Add performance information
        if response.processing_time:
            result['performance'] = {
                'processing_time': response.processing_time,
                'processing_time_ms': round(response.processing_time * 1000, 2)
            }
        
        # Add correlation ID for tracking
        if response.correlation_id:
            result['correlation_id'] = response.correlation_id
        
        return result
    
    def _format_xml(self, response: APIResponse) -> Dict[str, Any]:
        """Format response as XML structure"""
        # For now, return JSON structure with XML content type
        # TODO: Implement proper XML formatting
        json_response = self._format_json(response)
        
        try:
            import dicttoxml
            xml_content = dicttoxml.dicttoxml(json_response, custom_root='response', attr_type=False)
            return {
                'content': xml_content.decode('utf-8'),
                'content_type': 'application/xml'
            }
        except ImportError:
            # Fallback to JSON if XML library not available
            self.logger.warning("XML formatting requested but dicttoxml not available")
            return self._format_json(response)
    
    def _format_text(self, response: APIResponse) -> Dict[str, Any]:
        """Format response as plain text"""
        if response.is_success():
            if isinstance(response.data, str):
                content = response.data
            else:
                content = str(response.data)
        else:
            content = f"Error: {response.error}"
        
        return {
            'content': content,
            'content_type': 'text/plain'
        }
    
    def _serialize_data(self, data: Any) -> Any:
        """Serialize data for JSON output"""
        if isinstance(data, (str, int, float, bool, type(None))):
            return data
        elif isinstance(data, (list, tuple)):
            return [self._serialize_data(item) for item in data]
        elif isinstance(data, dict):
            return {key: self._serialize_data(value) for key, value in data.items()}
        elif hasattr(data, 'to_dict'):
            return data.to_dict()
        elif hasattr(data, '__dict__'):
            return {key: self._serialize_data(value) for key, value in data.__dict__.items()
                   if not key.startswith('_')}
        else:
            # Fallback to string representation
            return str(data)
    
    def _format_error_fallback(self, response: APIResponse, error: str) -> Dict[str, Any]:
        """Fallback error formatting when main formatting fails"""
        return {
            'success': False,
            'status': response.status.value,
            'error': {
                'message': response.error or "Internal formatting error",
                'code': response.error_code or "FORMATTING_ERROR",
                'details': {'formatting_error': error}
            },
            'timestamp': datetime.fromtimestamp(response.timestamp).isoformat(),
            'correlation_id': response.correlation_id
        }
    
    def format_success_response(self, data: Any, metadata: Dict[str, Any] = None,
                              correlation_id: str = None) -> Dict[str, Any]:
        """
        Create and format a successful response
        
        Args:
            data: Response data
            metadata: Optional metadata
            correlation_id: Request correlation ID
            
        Returns:
            Formatted success response
        """
        response = APIResponse(
            status=HTTPStatus.OK,
            data=data,
            metadata=metadata or {},
            correlation_id=correlation_id
        )
        
        return self.format_response(response)
    
    def format_error_response(self, status: HTTPStatus, error: str, 
                            error_code: str = None, error_details: Dict[str, Any] = None,
                            correlation_id: str = None) -> Dict[str, Any]:
        """
        Create and format an error response
        
        Args:
            status: HTTP status code
            error: Error message
            error_code: Error code
            error_details: Additional error details
            correlation_id: Request correlation ID
            
        Returns:
            Formatted error response
        """
        response = APIResponse(
            status=status,
            error=error,
            error_code=error_code,
            error_details=error_details,
            correlation_id=correlation_id
        )
        
        return self.format_response(response)
    
    def format_validation_error(self, validation_errors: Dict[str, str],
                              correlation_id: str = None) -> Dict[str, Any]:
        """
        Format validation error response
        
        Args:
            validation_errors: Dictionary of field -> error message
            correlation_id: Request correlation ID
            
        Returns:
            Formatted validation error response
        """
        return self.format_error_response(
            status=HTTPStatus.BAD_REQUEST,
            error="Validation failed",
            error_code="VALIDATION_ERROR",
            error_details={'validation_errors': validation_errors},
            correlation_id=correlation_id
        )
    
    def format_not_found_error(self, resource: str, correlation_id: str = None) -> Dict[str, Any]:
        """
        Format not found error response
        
        Args:
            resource: Resource that was not found
            correlation_id: Request correlation ID
            
        Returns:
            Formatted not found error response
        """
        return self.format_error_response(
            status=HTTPStatus.NOT_FOUND,
            error=f"Resource not found: {resource}",
            error_code="NOT_FOUND",
            correlation_id=correlation_id
        )
    
    def format_unauthorized_error(self, correlation_id: str = None) -> Dict[str, Any]:
        """
        Format unauthorized error response
        
        Args:
            correlation_id: Request correlation ID
            
        Returns:
            Formatted unauthorized error response
        """
        return self.format_error_response(
            status=HTTPStatus.UNAUTHORIZED,
            error="Authentication required",
            error_code="UNAUTHORIZED",
            correlation_id=correlation_id
        )
    
    def format_forbidden_error(self, resource: str = None, correlation_id: str = None) -> Dict[str, Any]:
        """
        Format forbidden error response
        
        Args:
            resource: Resource that access was denied to
            correlation_id: Request correlation ID
            
        Returns:
            Formatted forbidden error response
        """
        error_msg = f"Access denied to resource: {resource}" if resource else "Access denied"
        
        return self.format_error_response(
            status=HTTPStatus.FORBIDDEN,
            error=error_msg,
            error_code="FORBIDDEN",
            correlation_id=correlation_id
        )
    
    def format_rate_limit_error(self, retry_after: int = None, correlation_id: str = None) -> Dict[str, Any]:
        """
        Format rate limit error response
        
        Args:
            retry_after: Seconds until retry is allowed
            correlation_id: Request correlation ID
            
        Returns:
            Formatted rate limit error response
        """
        error_details = {}
        if retry_after:
            error_details['retry_after'] = retry_after
        
        return self.format_error_response(
            status=HTTPStatus.TOO_MANY_REQUESTS,
            error="Rate limit exceeded",
            error_code="RATE_LIMIT_EXCEEDED",
            error_details=error_details,
            correlation_id=correlation_id
        )
    
    def add_formatter(self, format_name: str, formatter_func):
        """
        Add custom response formatter
        
        Args:
            format_name: Name of the format
            formatter_func: Function that takes APIResponse and returns formatted dict
        """
        self.formatters[format_name] = formatter_func
        self.logger.debug(f"Added custom formatter: {format_name}")
    
    def get_supported_formats(self) -> list:
        """Get list of supported output formats"""
        return list(self.formatters.keys())
    
    def set_default_format(self, format_name: str):
        """Set default output format"""
        if format_name in self.formatters:
            self.default_format = format_name
            self.logger.debug(f"Set default format to: {format_name}")
        else:
            raise ValueError(f"Unsupported format: {format_name}")
    
    def determine_format_from_request(self, request) -> str:
        """
        Determine output format from request headers or parameters
        
        Args:
            request: APIRequest object
            
        Returns:
            Format name
        """
        # Check Accept header
        accept_header = request.get_header('Accept', '')
        
        if 'application/json' in accept_header:
            return 'json'
        elif 'application/xml' in accept_header:
            return 'xml'
        elif 'text/plain' in accept_header:
            return 'text'
        
        # Check format parameter
        format_param = request.params.get('format', '')
        if format_param in self.formatters:
            return format_param
        
        # Default format
        return self.default_format 