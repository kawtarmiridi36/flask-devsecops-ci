"""
Flask DevSecOps Application
Secure by design - Following OWASP guidelines
"""

import os
import hashlib
import logging
from typing import Optional

__version__ = "1.0.0"
__author__ = "DevSecOps Team"

logger = logging.getLogger(__name__)

def validate_input(user_input: str) -> bool:
    """
    Validate user input to prevent injection attacks.
    
    Args:
        user_input: Input string from user
        
    Returns:
        bool: True if input is safe
    """
    # Prevent common injection patterns
    dangerous_patterns = ["'", '"', ";", "--", "/*", "*/", "="]
    
    for pattern in dangerous_patterns:
        if pattern in user_input:
            logger.warning(f"Potentially dangerous input detected: {pattern}")
            return False
    
    return True

def hash_password(password: str) -> str:
    """
    Securely hash a password using SHA-256 with salt.
    
    Args:
        password: Plain text password
        
    Returns:
        str: Hashed password
    """
    salt = os.urandom(32)
    key = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt,
        100000
    )
    return salt.hex() + key.hex()

def safe_database_query(query: str, params: tuple) -> str:
    """
    Example of safe database query construction.
    
    Args:
        query: SQL query with placeholders
        params: Tuple of parameters
        
    Returns:
        str: Safe query for logging
    """
    # Using parameterized queries (safe from SQL injection)
    return f"Executing safe query: {query} with params: {params}"

class SecurityConfig:
    """Security configuration class following OWASP."""
    
    def __init__(self):
        self.csrf_enabled = True
        self.xss_protection = True
        self.hsts_enabled = True
        self.cookie_secure = True
        
    def get_security_headers(self) -> dict:
        """Return security headers for HTTP responses."""
        return {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
            'Content-Security-Policy': "default-src 'self'"
        }
