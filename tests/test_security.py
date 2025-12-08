"""
Security tests for DevSecOps pipeline.
"""

import pytest
from app import validate_input, hash_password, SecurityConfig

def test_input_validation_safe():
    """Test safe input validation."""
    assert validate_input("hello world") == True
    assert validate_input("test123") == True

def test_input_validation_unsafe():
    """Test unsafe input detection."""
    assert validate_input("test'; DROP TABLE users; --") == False
    assert validate_input('test" OR "1"="1') == False
    assert validate_input("test; ls -la") == False

def test_password_hashing():
    """Test password hashing produces different outputs."""
    password = "MySecurePassword123!"
    hash1 = hash_password(password)
    hash2 = hash_password(password)
    
    # Hashes should be different (different salt)
    assert hash1 != hash2
    # But same structure
    assert len(hash1) == len(hash2) == 128

def test_security_headers():
    """Test security headers configuration."""
    config = SecurityConfig()
    headers = config.get_security_headers()
    
    assert 'X-Content-Type-Options' in headers
    assert headers['X-Frame-Options'] == 'DENY'
    assert 'Content-Security-Policy' in headers

def test_security_config():
    """Test security configuration."""
    config = SecurityConfig()
    assert config.csrf_enabled == True
    assert config.xss_protection == True
    assert config.cookie_secure == True

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
