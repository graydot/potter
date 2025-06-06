#!/usr/bin/env python3
"""
Text Processing Plugins
Core plugins for text processing functionality
"""

import re
import logging
from typing import Dict, Any, List

from ..plugin_interface import TextProcessingPlugin, PluginContext

logger = logging.getLogger(__name__)


class TextFormatterPlugin(TextProcessingPlugin):
    """
    Plugin for basic text formatting operations
    
    Capabilities:
    - Text normalization (whitespace, line breaks)
    - Case transformations
    - Text cleanup and sanitization
    - Basic formatting operations
    """
    
    def get_plugin_info(self) -> Dict[str, Any]:
        """Return plugin metadata"""
        return {
            'name': 'TextFormatter',
            'version': '1.0.0',
            'description': 'Basic text formatting and normalization operations',
            'author': 'Potter Team',
            'categories': ['text_processing', 'formatting'],
            'keywords': ['format', 'normalize', 'cleanup', 'text'],
            'dependencies': []
        }
    
    def initialize(self, context: PluginContext) -> bool:
        """Initialize the text formatter plugin"""
        try:
            self.context = context
            self.logger = context.logger
            self.is_initialized = True
            
            self.logger.info("TextFormatter plugin initialized")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize TextFormatter plugin: {e}")
            return False
    
    def cleanup(self) -> None:
        """Cleanup plugin resources"""
        self.logger.info("TextFormatter plugin cleaned up")
    
    def get_capabilities(self) -> List[str]:
        """Return plugin capabilities"""
        return ['text_processing', 'text_formatting', 'text_normalization']
    
    def process_text(self, text: str, options: Dict[str, Any] = None) -> str:
        """
        Process text with formatting operations
        
        Args:
            text: Input text to process
            options: Processing options
            
        Returns:
            Formatted text
        """
        if not options:
            options = {}
        
        result = text
        
        # Normalize whitespace
        if options.get('normalize_whitespace', True):
            result = self._normalize_whitespace(result)
        
        # Fix line breaks
        if options.get('fix_line_breaks', True):
            result = self._fix_line_breaks(result)
        
        # Apply case transformation
        case_transform = options.get('case_transform')
        if case_transform:
            result = self._apply_case_transform(result, case_transform)
        
        # Remove extra punctuation
        if options.get('cleanup_punctuation', False):
            result = self._cleanup_punctuation(result)
        
        # Trim text
        if options.get('trim', True):
            result = result.strip()
        
        return result
    
    def execute_text_formatting(self, text: str, format_type: str, **kwargs) -> str:
        """Execute specific formatting operation"""
        if format_type == 'normalize':
            return self._normalize_whitespace(text)
        elif format_type == 'uppercase':
            return text.upper()
        elif format_type == 'lowercase':
            return text.lower()
        elif format_type == 'title':
            return text.title()
        elif format_type == 'sentence':
            return self._sentence_case(text)
        elif format_type == 'cleanup':
            return self._cleanup_text(text)
        else:
            raise ValueError(f"Unsupported format type: {format_type}")
    
    def execute_text_normalization(self, text: str, **kwargs) -> str:
        """Execute text normalization"""
        options = {
            'normalize_whitespace': True,
            'fix_line_breaks': True,
            'trim': True,
            **kwargs
        }
        return self.process_text(text, options)
    
    def _normalize_whitespace(self, text: str) -> str:
        """Normalize whitespace in text"""
        # Replace multiple spaces with single space
        text = re.sub(r' +', ' ', text)
        
        # Replace tabs with spaces
        text = text.replace('\t', ' ')
        
        # Remove trailing spaces from lines
        text = '\n'.join(line.rstrip() for line in text.split('\n'))
        
        return text
    
    def _fix_line_breaks(self, text: str) -> str:
        """Fix and normalize line breaks"""
        # Normalize line endings
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        
        # Remove excessive blank lines (more than 2 consecutive)
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        return text
    
    def _apply_case_transform(self, text: str, transform: str) -> str:
        """Apply case transformation"""
        if transform == 'upper':
            return text.upper()
        elif transform == 'lower':
            return text.lower()
        elif transform == 'title':
            return text.title()
        elif transform == 'sentence':
            return self._sentence_case(text)
        else:
            return text
    
    def _sentence_case(self, text: str) -> str:
        """Convert to sentence case"""
        if not text:
            return text
        
        # Capitalize first letter of text
        result = text[0].upper() + text[1:].lower()
        
        # Capitalize after sentence endings
        result = re.sub(r'([.!?]\s+)([a-z])', lambda m: m.group(1) + m.group(2).upper(), result)
        
        return result
    
    def _cleanup_punctuation(self, text: str) -> str:
        """Clean up excessive punctuation"""
        # Remove multiple consecutive punctuation marks
        text = re.sub(r'[.]{2,}', '...', text)  # Multiple periods to ellipsis
        text = re.sub(r'[!]{2,}', '!', text)    # Multiple exclamations to single
        text = re.sub(r'[?]{2,}', '?', text)    # Multiple questions to single
        text = re.sub(r'[,]{2,}', ',', text)    # Multiple commas to single
        
        return text
    
    def _cleanup_text(self, text: str) -> str:
        """General text cleanup"""
        # Remove zero-width characters
        text = re.sub(r'[\u200b-\u200d\ufeff]', '', text)
        
        # Remove excessive punctuation
        text = self._cleanup_punctuation(text)
        
        # Normalize whitespace
        text = self._normalize_whitespace(text)
        
        # Fix line breaks
        text = self._fix_line_breaks(text)
        
        return text.strip()


class TextValidatorPlugin(TextProcessingPlugin):
    """
    Plugin for text validation operations
    
    Capabilities:
    - Length validation
    - Content validation
    - Format validation
    - Language detection
    """
    
    def get_plugin_info(self) -> Dict[str, Any]:
        """Return plugin metadata"""
        return {
            'name': 'TextValidator',
            'version': '1.0.0',
            'description': 'Text validation and content checking operations',
            'author': 'Potter Team',
            'categories': ['text_processing', 'validation'],
            'keywords': ['validate', 'check', 'content', 'text'],
            'dependencies': []
        }
    
    def initialize(self, context: PluginContext) -> bool:
        """Initialize the text validator plugin"""
        try:
            self.context = context
            self.logger = context.logger
            self.is_initialized = True
            
            # Load validation rules from config
            self.max_length = context.get_config('max_text_length', 10000)
            self.min_length = context.get_config('min_text_length', 1)
            self.allowed_languages = context.get_config('allowed_languages', ['en'])
            
            self.logger.info("TextValidator plugin initialized")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize TextValidator plugin: {e}")
            return False
    
    def cleanup(self) -> None:
        """Cleanup plugin resources"""
        self.logger.info("TextValidator plugin cleaned up")
    
    def get_capabilities(self) -> List[str]:
        """Return plugin capabilities"""
        return ['text_processing', 'text_validation', 'content_validation']
    
    def process_text(self, text: str, options: Dict[str, Any] = None) -> str:
        """
        Validate text and return validation results
        
        Args:
            text: Input text to validate
            options: Validation options
            
        Returns:
            Validation result as JSON string
        """
        if not options:
            options = {}
        
        validation_result = self.validate_text(text, options)
        
        # Return text if valid, or raise exception if invalid
        if validation_result['is_valid']:
            return text
        else:
            raise ValueError(f"Text validation failed: {validation_result['errors']}")
    
    def validate_text(self, text: str, options: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Validate text against various criteria
        
        Args:
            text: Text to validate
            options: Validation options
            
        Returns:
            Validation result dictionary
        """
        if not options:
            options = {}
        
        errors = []
        warnings = []
        
        # Length validation
        max_len = options.get('max_length', self.max_length)
        min_len = options.get('min_length', self.min_length)
        
        if len(text) > max_len:
            errors.append(f"Text too long: {len(text)} > {max_len}")
        
        if len(text) < min_len:
            errors.append(f"Text too short: {len(text)} < {min_len}")
        
        # Content validation
        if options.get('require_alphanumeric', False):
            if not re.search(r'[a-zA-Z0-9]', text):
                errors.append("Text must contain alphanumeric characters")
        
        if options.get('no_special_chars', False):
            if re.search(r'[<>{}[\]|\\`~]', text):
                errors.append("Text contains prohibited special characters")
        
        # Format validation
        if options.get('no_urls', False):
            url_pattern = r'https?://[^\s]+|www\.[^\s]+|[^\s]+\.[a-z]{2,}'
            if re.search(url_pattern, text, re.IGNORECASE):
                warnings.append("Text contains URLs")
        
        if options.get('no_emails', False):
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            if re.search(email_pattern, text):
                warnings.append("Text contains email addresses")
        
        # Language detection (simplified)
        if options.get('check_language', False):
            detected_lang = self._detect_language(text)
            allowed_langs = options.get('allowed_languages', self.allowed_languages)
            if detected_lang not in allowed_langs:
                warnings.append(f"Detected language '{detected_lang}' not in allowed list")
        
        # Profanity check (simplified)
        if options.get('check_profanity', False):
            if self._contains_profanity(text):
                errors.append("Text contains inappropriate content")
        
        return {
            'is_valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'text_length': len(text),
            'word_count': len(text.split()),
            'line_count': len(text.split('\n'))
        }
    
    def execute_text_validation(self, text: str, validation_type: str, **kwargs) -> tuple[bool, str]:
        """Execute specific validation operation"""
        if validation_type == 'length':
            max_len = kwargs.get('max_length', self.max_length)
            min_len = kwargs.get('min_length', self.min_length)
            if len(text) > max_len:
                return False, f"Text too long: {len(text)} > {max_len}"
            if len(text) < min_len:
                return False, f"Text too short: {len(text)} < {min_len}"
            return True, "Length validation passed"
        
        elif validation_type == 'content':
            result = self.validate_text(text, kwargs)
            return result['is_valid'], '; '.join(result['errors']) if result['errors'] else "Content validation passed"
        
        elif validation_type == 'format':
            # Basic format validation
            if not text.strip():
                return False, "Text is empty or whitespace only"
            return True, "Format validation passed"
        
        else:
            raise ValueError(f"Unsupported validation type: {validation_type}")
    
    def _detect_language(self, text: str) -> str:
        """
        Simple language detection (placeholder implementation)
        
        In a real implementation, this would use a proper language detection library
        """
        # Very basic heuristic - just return English for now
        # TODO: Implement proper language detection
        return 'en'
    
    def _contains_profanity(self, text: str) -> bool:
        """
        Simple profanity check (placeholder implementation)
        
        In a real implementation, this would use a proper profanity filter
        """
        # Very basic profanity check - just a few examples
        profanity_words = ['spam', 'scam', 'fake']  # Simplified list
        text_lower = text.lower()
        
        for word in profanity_words:
            if word in text_lower:
                return True
        
        return False 