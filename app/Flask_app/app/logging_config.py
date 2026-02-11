import logging
import sys

def setup_logging(app):
    """Setup logging to stdout for Kubernetes/Loki"""
    
    # Remove default handlers
    app.logger.handlers.clear()
    
    # Create stdout handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    
    # Add handler to logger
    app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO)
    
    # Also set werkzeug logger
    werkzeug_logger = logging.getLogger('werkzeug')
    werkzeug_logger.handlers.clear()
    werkzeug_logger.addHandler(handler)
    werkzeug_logger.setLevel(logging.INFO)
    
    return app
