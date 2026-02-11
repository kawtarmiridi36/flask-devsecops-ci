# app/Flask_app/app/metrics.py
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from flask import Response, request
import time
from datetime import datetime

# Define Prometheus metrics
REQUEST_COUNT = Counter(
    'flask_http_request_total',
    'Total HTTP Requests',
    ['method', 'endpoint', 'http_status']
)

REQUEST_LATENCY = Histogram(
    'flask_http_request_duration_seconds',
    'HTTP Request Latency',
    ['method', 'endpoint']
)

ACTIVE_USERS = Gauge(
    'flask_active_users',
    'Number of active users'
)

HEALTH_STATUS = Gauge(
    'flask_health_status',
    'Application health status (1=healthy, 0=unhealthy)'
)

DATABASE_CONNECTIONS = Gauge(
    'flask_db_connections',
    'Number of database connections'
)

ERROR_COUNT = Counter(
    'flask_http_errors_total',
    'Total HTTP Errors',
    ['error_type']
)

# Custom metrics for your application
ANNOUNCEMENT_COUNT = Counter(
    'flask_announcements_total',
    'Total announcements created'
)

USER_REGISTRATIONS = Counter(
    'flask_user_registrations_total',
    'Total user registrations'
)

COMMENT_COUNT = Counter(
    'flask_comments_total',
    'Total comments created'
)

def monitor_request_start_time():
    """Store start time for request latency calculation"""
    request.start_time = time.time()

def record_request_metrics(response):
    """Record metrics after each request"""
    # Calculate request latency
    if hasattr(request, 'start_time'):
        request_latency = time.time() - request.start_time
        REQUEST_LATENCY.labels(
            method=request.method,
            endpoint=request.endpoint or request.path
        ).observe(request_latency)
    
    # Count requests
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.endpoint or request.path,
        http_status=response.status_code
    ).inc()
    
    # Count errors
    if response.status_code >= 400:
        ERROR_COUNT.labels(error_type=str(response.status_code)).inc()
    
    return response

def setup_metrics(app):
    """Setup Prometheus metrics middleware for Flask app"""
    
    @app.before_request
    def before_request():
        monitor_request_start_time()
    
    @app.after_request
    def after_request(response):
        return record_request_metrics(response)
    
    @app.route('/metrics')
    def metrics():
        """Expose Prometheus metrics endpoint"""
        # Update health status
        HEALTH_STATUS.set(1)  # Assuming healthy
        
        return Response(
            generate_latest(),
            mimetype=CONTENT_TYPE_LATEST,
            headers={
                'Cache-Control': 'no-cache, no-store, must-revalidate',
                'Pragma': 'no-cache',
                'Expires': '0'
            }
        )
    
    # Add custom metrics update functions
    def increment_announcement_count():
        ANNOUNCEMENT_COUNT.inc()
    
    def increment_user_registration():
        USER_REGISTRATIONS.inc()
    
    def increment_comment_count():
        COMMENT_COUNT.inc()
    
    # Make functions available to the app
    app.increment_announcement_count = increment_announcement_count
    app.increment_user_registration = increment_user_registration
    app.increment_comment_count = increment_comment_count
    
    return app

# Utility function to update active users (you can call this from your app)
def update_active_users(count):
    """Update active users gauge"""
    ACTIVE_USERS.set(count)

def update_database_connections(count):
    """Update database connections gauge"""
    DATABASE_CONNECTIONS.set(count)
