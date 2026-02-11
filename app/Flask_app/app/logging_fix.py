import logging
import sys

def setup_app_logging(app):
    """
    Setup logging for Flask app that works with gunicorn workers.
    Logs only to stdout (for Kubernetes/Loki).
    """
    # Remove all existing handlers
    for handler in app.logger.handlers[:]:
        app.logger.removeHandler(handler)
    
    # Create a stream handler for stdout
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    handler.setFormatter(formatter)
    
    # Add handler to app logger
    app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO)
    
    # Don't propagate to root logger
    app.logger.propagate = False
    
    # Also configure werkzeug logger if it exists
    try:
        werkzeug_logger = logging.getLogger('werkzeug')
        for h in werkzeug_logger.handlers[:]:
            werkzeug_logger.removeHandler(h)
        werkzeug_logger.addHandler(handler)
        werkzeug_logger.setLevel(logging.INFO)
        werkzeug_logger.propagate = False
    except:
        pass
    
    return app
