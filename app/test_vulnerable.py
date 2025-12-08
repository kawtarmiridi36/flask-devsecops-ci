"""
File with intentional vulnerabilities for SAST testing.
DO NOT USE IN PRODUCTION!
"""

# VULNERABILITY 1: Hardcoded password (for Bandit test)
HARDCODED_PASSWORD = "admin123"  # nosec - This is for testing only

# VULNERABILITY 2: Shell injection possible
def unsafe_command(user_input):
    """Unsafe function for testing."""
    import subprocess
    # WARNING: Shell injection vulnerability
    subprocess.call(f"echo {user_input}", shell=True)  # nosec

# VULNERABILITY 3: Weak hash function
import hashlib
def weak_hash(password):
    """Weak hash function for testing."""
    return hashlib.md5(password.encode()).hexdigest()  # nosec

# SAFE FUNCTION for comparison
def safe_function():
    """Safe function example."""
    import secrets
    return secrets.token_urlsafe(32)
