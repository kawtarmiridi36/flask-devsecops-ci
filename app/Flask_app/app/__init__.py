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

    # Créer l'app avec le chemin custom des templates
    app = Flask(__name__, template_folder=template_dir)
    app.config.from_object(Config)

    # Configuration de la journalisation
    if not app.debug and not app.testing:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = RotatingFileHandler(
            'logs/app.log', maxBytes=10240, backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('🚀 Démarrage de l application Flask')

    print("🚀 Initialisation de l'application Flask...")

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

    # Enregistrement des blueprints
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
        app.logger.info('Blueprints enregistrés: auth, annonces, comments, members')

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
        app.logger.info('Interface développeur activée: /dev')
    except Exception as e:
        error_msg = f"Erreur interface dev: {e}"
        print(f"❌ {error_msg}")
        app.logger.error(error_msg)

        @app.route('/dev')
        def dev_fallback():
            app.logger.warning('Accès à l interface dev en mode fallback')
            return "<h1>Dev Interface</h1><p>Version fallback - Erreur import</p>"

    # ⚠️ Exempter les blueprints API de la protection CSRF
    # (les formulaires utilisent fetch() + JSON sans token CSRF)
    try:
        csrf.exempt(auth_bp)
        csrf.exempt(annonces_bp)
        csrf.exempt(comments_bp)
        csrf.exempt(members_bp)
        csrf.exempt(dev_bp)
    except Exception as e:
        # Si un blueprint n'est pas défini à cause d'une erreur d'import, on ignore
        app.logger.warning(f"CSRF exempt error (non-bloquant): {e}")

    @app.route('/health')
    def health():
        app.logger.info('Health check appelé')
        return jsonify({
            'status': 'healthy',
            'dev_interface': 'active',
            'logging': 'enabled',
            'csrf': 'enabled (API exemptées)'
        })

    @app.route('/')
    def index():
        try:
            app.logger.info('Accès à la page d accueil')
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
            </ul>
            """

    @app.route('/dev-test')
    def dev_test():
        app.logger.info('Test dev appelé')
        return jsonify({
            'test': 'success',
            'message': 'Dev test route works',
            'features': {
                'logging': 'active',
                'csrf': 'active (API exemptées)',
                'database': 'connected'
            }
        })

    # Route pour les erreurs 404
    @app.errorhandler(404)
    def not_found_error(error):
        app.logger.warning(f'404 - Page non trouvée: {request.url}')
        return jsonify({'error': 'Page not found'}), 404

    # Route pour les erreurs 500
    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f'500 - Erreur interne: {error}')
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500

    # Routes pour l'interface utilisateur (HTML)
    @app.route('/auth/login', methods=['GET'])
    def login_page():
        """Page HTML de connexion"""
        return render_template('auth/login.html')

    @app.route('/auth/register', methods=['GET'])
    def register_page():
        """Page HTML d'inscription"""
        return render_template('auth/register.html')

    @app.route('/annonces', methods=['GET'])
    def annonces_page():
        """Page HTML des annonces"""
        return render_template('annonces.html')

    print("🎯 Application prête!")
    app.logger.info('Application Flask initialisée avec succès')

    return app
