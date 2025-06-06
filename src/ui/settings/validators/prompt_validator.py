#!/usr/bin/env python3
"""
Prompt Validator
Handles validation of prompt names and content
"""

import logging
from typing import Tuple, Optional, List

logger = logging.getLogger(__name__)


class PromptValidator:
    """Validates prompt names and content"""
    
    MAX_NAME_LENGTH = 10
    MIN_NAME_LENGTH = 1
    MAX_PROMPT_LENGTH = 5000
    MIN_PROMPT_LENGTH = 10
    
    # Reserved names that cannot be used
    RESERVED_NAMES = {'default', 'system', 'none', 'null', 'undefined'}
    
    def validate_name(self, name: str, existing_names: List[str], 
                      exclude_index: Optional[int] = None) -> Tuple[bool, Optional[str]]:
        """
        Validate a prompt name
        
        Args:
            name: The prompt name to validate
            existing_names: List of existing prompt names
            exclude_index: Index to exclude from duplicate check (for editing)
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not name:
            return False, "Prompt name cannot be empty"
        
        # Strip whitespace
        name = name.strip()
        
        # Check length
        if len(name) < self.MIN_NAME_LENGTH:
            return False, f"Prompt name must be at least {self.MIN_NAME_LENGTH} character"
        
        if len(name) > self.MAX_NAME_LENGTH:
            return False, f"Prompt name must be {self.MAX_NAME_LENGTH} characters or less"
        
        # Check if alphanumeric (allow underscores)
        if not name.replace('_', '').isalnum():
            return False, "Prompt name must contain only letters, numbers, and underscores"
        
        # Check reserved names
        if name.lower() in self.RESERVED_NAMES:
            return False, f"'{name}' is a reserved name and cannot be used"
        
        # Check for duplicates
        names_to_check = existing_names.copy()
        if exclude_index is not None and 0 <= exclude_index < len(names_to_check):
            names_to_check.pop(exclude_index)
        
        if name.lower() in [n.lower() for n in names_to_check]:
            return False, f"A prompt named '{name}' already exists"
        
        return True, None
    
    def validate_content(self, content: str) -> Tuple[bool, Optional[str]]:
        """
        Validate prompt content
        
        Args:
            content: The prompt content to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not content:
            return False, "Prompt content cannot be empty"
        
        # Strip whitespace
        content = content.strip()
        
        # Check minimum length
        if len(content) < self.MIN_PROMPT_LENGTH:
            return False, f"Prompt must be at least {self.MIN_PROMPT_LENGTH} characters"
        
        # Check maximum length
        if len(content) > self.MAX_PROMPT_LENGTH:
            return False, f"Prompt must be {self.MAX_PROMPT_LENGTH} characters or less"
        
        # Check for placeholder text
        placeholder_texts = [
            "enter prompt here",
            "type your prompt",
            "prompt text",
            "your prompt here"
        ]
        
        if content.lower() in placeholder_texts:
            return False, "Please enter a meaningful prompt"
        
        return True, None
    
    def sanitize_name(self, name: str) -> str:
        """
        Sanitize a prompt name by removing invalid characters
        
        Args:
            name: The name to sanitize
            
        Returns:
            Sanitized name
        """
        # Remove non-alphanumeric characters except underscores
        sanitized = ''.join(c for c in name if c.isalnum() or c == '_')
        
        # Truncate to max length
        if len(sanitized) > self.MAX_NAME_LENGTH:
            sanitized = sanitized[:self.MAX_NAME_LENGTH]
        
        return sanitized 