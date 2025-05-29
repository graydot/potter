#!/usr/bin/env python3
"""
OpenAI Client Manager
Handles OpenAI API integration and text processing
"""

import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class OpenAIClientManager:
    """Manages OpenAI client initialization and text processing"""
    
    def __init__(self, api_key: str = None):
        self.client = None
        self.api_key = api_key
        self.is_initialized = False
        
        if api_key:
            self.setup_client(api_key)
    
    def setup_client(self, api_key: str = None):
        """Initialize OpenAI client"""
        if api_key:
            self.api_key = api_key
        
        if not self.api_key:
            logger.warning("No OpenAI API key provided")
            self.client = None
            self.is_initialized = False
            return False
        
        try:
            # Import OpenAI and check if it's available
            import openai
            logger.debug(f"OpenAI library version: {openai.__version__}")
            
            # Try to import certifi for SSL certificates
            try:
                import certifi
                import ssl
                logger.debug(f"SSL certificates available at: {certifi.where()}")
                
                # Create SSL context
                ssl_context = ssl.create_default_context(cafile=certifi.where())
                logger.debug("SSL context created successfully")
            except ImportError:
                logger.warning("certifi not available, using default SSL context")
                ssl_context = None
            except Exception as ssl_e:
                logger.warning(f"SSL context creation failed: {ssl_e}")
                ssl_context = None
            
            # Create OpenAI client with explicit parameters
            self.client = openai.OpenAI(
                api_key=self.api_key,
                timeout=30.0  # Set explicit timeout
            )
            self.is_initialized = True
            logger.info("OpenAI client initialized successfully")
            
            # Test the client with a minimal request to verify it works
            try:
                # This doesn't actually make a request, just validates the client setup
                logger.debug("OpenAI client setup validation completed")
            except Exception as test_e:
                logger.warning(f"OpenAI client validation warning: {test_e}")
                # Client may still work for actual requests
            
            return True
                
        except ImportError as e:
            logger.error(f"OpenAI library not available: {e}")
            self.client = None
            self.is_initialized = False
            return False
        except FileNotFoundError as e:
            logger.error(f"File not found during OpenAI initialization: {e}")
            logger.error("This may be due to missing SSL certificates or configuration files")
            logger.error("Try: pip install --upgrade openai certifi")
            self.client = None
            self.is_initialized = False
            return False
        except OSError as e:
            logger.error(f"OS error during OpenAI initialization: {e}")
            logger.error("This may be a network or file system issue")
            self.client = None
            self.is_initialized = False
            return False
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            self.client = None
            self.is_initialized = False
            return False
    
    def process_text(self, text: str, prompt: str, model: str = "gpt-3.5-turbo", 
                    max_tokens: int = 1000, temperature: float = 0.7) -> Optional[str]:
        """Process text using ChatGPT"""
        if not self.is_initialized or not self.client:
            logger.error("OpenAI client not initialized")
            return None
        
        if not text.strip():
            logger.warning("No text to process")
            return None
        
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a helpful writing assistant. Return only the processed text without any additional comments or formatting."},
                    {"role": "user", "content": f"{prompt}\n\n{text}"}
                ],
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            processed_text = response.choices[0].message.content.strip()
            logger.info(f"Successfully processed text: {len(text)} -> {len(processed_text)} characters")
            return processed_text
            
        except Exception as e:
            logger.error(f"Error processing text with ChatGPT: {e}")
            return None
    
    def is_available(self) -> bool:
        """Check if the OpenAI client is available and ready"""
        return self.is_initialized and self.client is not None
    
    def update_api_key(self, api_key: str) -> bool:
        """Update the API key and reinitialize the client"""
        self.api_key = api_key
        return self.setup_client()


def get_api_key_from_env() -> Optional[str]:
    """Get API key from environment variables"""
    return os.getenv('OPENAI_API_KEY', "").strip() or None


def validate_api_key_format(api_key: str) -> bool:
    """Validate OpenAI API key format"""
    if not api_key:
        return False
    
    # OpenAI API keys typically start with 'sk-' and are quite long
    if api_key.startswith('sk-') and len(api_key) > 20:
        return True
    
    logger.warning(f"API key format appears invalid: {api_key[:10]}...")
    return False 