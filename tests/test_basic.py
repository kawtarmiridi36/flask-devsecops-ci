"""
Basic functionality tests.
"""

def test_addition():
    """Basic math test."""
    assert 1 + 1 == 2

def test_string():
    """String test."""
    assert "dev" + "sec" + "ops" == "devsecops"

def test_list():
    """List test."""
    items = [1, 2, 3]
    assert len(items) == 3
    assert 2 in items
