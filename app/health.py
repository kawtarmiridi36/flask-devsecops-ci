"""
Health check module for Kubernetes probes
"""
import datetime
from flask import Blueprint, jsonify

health_bp = Blueprint('health', __name__)

@health_bp.route('/health')
def health_check():
    """Simple health endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.datetime.utcnow().isoformat(),
        'service': 'flask-devsecops',
        'version': '1.0.0'
    }), 200

@health_bp.route('/ready')
def readiness_check():
    """Readiness probe with dependency checks"""
    checks = {
        'api': True,
        'timestamp': datetime.datetime.utcnow().isoformat()
    }
    
    # Add database check if you have DB
    try:
        from sqlalchemy import text
        from .extensions import db
        db.session.execute(text('SELECT 1'))
        checks['database'] = True
    except:
        checks['database'] = False
    
    status_code = 200 if all(checks.get(k, True) for k in ['api', 'database']) else 503
    
    return jsonify(checks), status_code
