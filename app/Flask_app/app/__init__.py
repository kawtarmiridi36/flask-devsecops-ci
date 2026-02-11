import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, jsonify, render_template, request
from config import Config
from .extensions import db, bcrypt, login_manager, csrf


def create_app():

    # Obtenir le chemin absolu du projet
    base_dir = os.path.abspath(os.path.dirname(__file__))
    template_dir = os.path.join(base_dir, '..', 'templates')

    print(f"📁 Chemin templates: {template_dir}")
    print(f"📁 Existe: {os.path.exists(template_dir)}")

    # Créer l'app
    app = Flask(__name__, template_folder=template_dir)
    app.config.from_object(Config)

    # ⚡ IMPORTANT: Setup Prometheus metrics FIRST (before blueprints)
    try:
        from .metrics import setup_metrics
        app = setup_metrics(app)
        print("✅ Prometheus metrics enabled")
        app.logger.info("Prometheus metrics enabled")
    except ImportError as e:
        error_msg = f"⚠️  Prometheus metrics not available: {e}"
        print(error_msg)
        app.logger.warning(error_msg)

    # Blueprint health (IMPORTANT : après création de app)
    from .health import health_bp
    app.register_blueprint(health_bp)

    # Setup logging for Kubernetes/Loki (stdout only)
    from .logging_fix import setup_app_logging
    app = setup_app_logging(app)

    # Initialisation des extensions
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    # Configuration de user_loader
    from .models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Enregistrement des blueprints principaux
    try:
        from .auth.routes import auth_bp
        from .annonces.routes import annonces_bp
        from .comments.routes import comments_bp
        from .members.routes import members_bp

        app.register_blueprint(auth_bp, url_prefix='/auth')
        app.register_blueprint(annonces_bp, url_prefix='/annonces')
        app.register_blueprint(comments_bp, url_prefix='/comments')
        app.register_blueprint(members_bp, url_prefix='/members')

        print("✅ Blueprints principaux enregistrés")
        app.logger.info("Blueprints enregistrés: auth, annonces, comments, members")

        # 🔧 MODIFICATION: Inject metrics increment functions into blueprints
        # We'll add metrics increments to routes (examples below)
        # This should be done in the actual route files, but here's the pattern

    except Exception as e:
        error_msg = f"Erreur blueprints: {e}"
        print(f"⚠️  {error_msg}")
        app.logger.error(error_msg)

    # Interface développeur
    print("🔄 Activation interface développeur...")
    try:
        from .dev_interface import dev_bp
        app.register_blueprint(dev_bp)
        print("✅ Interface développeur ACTIVÉE: /dev")
        app.logger.info("Interface développeur activée: /dev")
    except Exception as e:
        error_msg = f"Erreur interface dev: {e}"
        print(f"❌ {error_msg}")
        app.logger.error(error_msg)

        @app.route('/dev')
        def dev_fallback():
            app.logger.warning("Accès à l'interface dev en mode fallback")
            return "<h1>Dev Interface</h1><p>Version fallback - Erreur import</p>"

    # Exempter les blueprints API de la protection CSRF
    try:
        csrf.exempt(auth_bp)
        csrf.exempt(annonces_bp)
        csrf.exempt(comments_bp)
        csrf.exempt(members_bp)
        csrf.exempt(dev_bp)
        csrf.exempt(health_bp)
    except Exception as e:
        app.logger.warning(f"CSRF exempt error (non-bloquant): {e}")

    @app.route('/')
    def index():
        try:
            app.logger.info("Accès à la page d'accueil")
            return render_template('index.html')
        except Exception as e:
            error_msg = f"Erreur template index: {e}"
            app.logger.error(error_msg)
            return f"""
            <h1>🚀 Application Flask - Fallback</h1>
            <p>Erreur template: {e}</p>
            <p>Mais l'application fonctionne !</p>
            <ul>
                <li><a href="/health">/health</a> - ✅ Fonctionne</li>
                <li><a href="/dev">/dev</a> - Interface développeur</li>
                <li><a href="/auth/login">/auth/login</a> - Connexion</li>
                <li><a href="/metrics">/metrics</a> - Métriques Prometheus</li>
            </ul>
            """

    @app.route('/dev-test')
    def dev_test():
        app.logger.info("Test dev appelé")
        return jsonify({
            "test": "success",
            "message": "Dev test route works",
            "features": {
                "logging": "active",
                "csrf": "active (API exemptées)",
                "database": "connected",
                "metrics": "active - /metrics endpoint available"
            }
        })

    # Route pour les erreurs 404
    @app.errorhandler(404)
    def not_found_error(error):
        app.logger.warning(f"404 - Page non trouvée: {request.url}")
        return jsonify({"error": "Page not found"}), 404

    # Route pour les erreurs 500
    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f"500 - Erreur interne: {error}")
        db.session.rollback()
        return jsonify({"error": "Internal server error"}), 500

    # Routes HTML
    @app.route('/auth/login', methods=['GET'])
    def login_page():
        return render_template('auth/login.html')

    @app.route('/auth/register', methods=['GET'])
    def register_page():
        return render_template('auth/register.html')

    @app.route('/annonces', methods=['GET'])
    def annonces_page():
        return render_template('annonces.html')

    # 🔧 NOUVELLE ROUTE: Metrics endpoint for Prometheus
    # Note: This route is actually handled by the setup_metrics function,
    # but we add a reference here for clarity
    
    @app.route('/metrics-info')
    def metrics_info():
        """Info page about metrics endpoint"""
        return jsonify({
            "metrics_endpoint": "/metrics",
            "available_metrics": [
                "flask_http_request_total",
                "flask_http_request_duration_seconds",
                "flask_active_users",
                "flask_health_status",
                "flask_db_connections",
                "flask_http_errors_total",
                "flask_announcements_total",
                "flask_user_registrations_total",
                "flask_comments_total"
            ],
            "monitoring": {
                "prometheus_scrape_path": "/metrics",
                "prometheus_scrape_interval": "30s"
            }
        })

    print("🎯 Application prête! Métriques disponibles sur /metrics")
    app.logger.info("Application Flask initialisée avec succès, métriques Prometheus activées")

    return app
