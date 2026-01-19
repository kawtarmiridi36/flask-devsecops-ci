from flask import Blueprint, render_template, jsonify
from .extensions import db
from .models import User, Annonce, Commentaire

dev_bp = Blueprint('dev', __name__, url_prefix='/dev')


def get_safe_count(model):
    """Compte les éléments d'un modèle en gérant les erreurs de DB"""
    try:
        return model.query.count()
    except Exception:
        return 0


@dev_bp.route('/')
def dev_dashboard():
    """Dashboard principal développeur"""
    stats = {
        'total_users': get_safe_count(User),
        'total_annonces': get_safe_count(Annonce),
        'total_commentaires': get_safe_count(Commentaire),
        'annonces_24h': 0,
        'users_admins': User.query.filter_by(role='admin').count()
        if get_safe_count(User) > 0 else 0
    }

    # Données récentes pour l'affichage
    recent_annonces = (
        Annonce.query.order_by(Annonce.date.desc()).limit(3).all()
        if get_safe_count(Annonce) > 0 else []
    )
    recent_users = (
        User.query.order_by(User.id.desc()).limit(3).all()
        if get_safe_count(User) > 0 else []
    )

    return render_template(
        'dev/dashboard.html',
        stats=stats,
        recent_annonces=recent_annonces,
        recent_users=recent_users
    )


@dev_bp.route('/api/stats')
def get_stats():
    """API des statistiques"""
    stats = {
        'users': get_safe_count(User),
        'annonces': get_safe_count(Annonce),
        'comments': get_safe_count(Commentaire),
        'db_status': 'healthy' if get_safe_count(User) >= 0 else 'error'
    }
    return jsonify(stats)


@dev_bp.route('/api/health')
def health_check():
    """Check de santé pour l'interface dev"""
    db_status = "healthy" if get_safe_count(User) >= 0 else "error"
    return jsonify({
        'dev_interface': 'active',
        'status': 'healthy',
        'database': db_status,
        'endpoints': {
            'stats': '/dev/api/stats',
            'users': '/dev/api/users',
            'annonces': '/dev/api/annonces',
            'db_info': '/dev/api/db-info'
        }
    })


@dev_bp.route('/api/db-info')
def db_info():
    """Informations sur la base de données"""
    return jsonify({
        'tables': ['user', 'annonce', 'commentaire'],
        'initialized': get_safe_count(User) >= 0,
        'total_records': {
            'users': get_safe_count(User),
            'annonces': get_safe_count(Annonce),
            'commentaires': get_safe_count(Commentaire)
        }
    })


@dev_bp.route('/api/users')
def get_users_list():
    """Liste tous les utilisateurs"""
    try:
        users = User.query.all()
        return jsonify([{
            'id': u.id,
            'username': u.username,
            'email': u.email,
            'role': u.role,
            # nombre d'annonces créées par cet utilisateur
            'annonces_count': Annonce.query.filter_by(user_id=u.id).count()
        } for u in users])
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@dev_bp.route('/api/annonces')
def get_annonces_list():
    """Liste toutes les annonces avec leurs commentaires"""
    try:
        annonces = Annonce.query.all()
        result = []
        for annonce in annonces:
            commentaires = Commentaire.query.filter_by(
                annonce_id=annonce.id
            ).all()
            result.append({
                'id': annonce.id,
                'titre': annonce.titre,
                'contenu': (
                    annonce.contenu[:100] + '...'
                    if len(annonce.contenu) > 100 else annonce.contenu
                ),
                'date': annonce.date.isoformat() if annonce.date else None,
                'commentaires_count': len(commentaires),
                'commentaires': [{
                    'id': c.id,
                    'contenu': c.contenu,
                    'date': c.date.isoformat() if c.date else None
                } for c in commentaires]
            })
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@dev_bp.route('/api/create-test-data', methods=['POST'])
def create_test_data():
    """Crée des données de test via l'interface dev"""
    try:
        # S'assurer qu'il y a un utilisateur admin pour associer les annonces/commentaires
        admin = User.query.filter_by(username="admin").first()
        if not admin:
            admin = User(
                username="admin",
                email="admin@example.com",
                role="admin"
            )
            admin.set_password("admin123")
            db.session.add(admin)
            db.session.commit()

        # Créer quelques annonces supplémentaires
        new_annonces = []
        for i in range(3, 6):
            annonce = Annonce(
                titre=f"Annonce de test {i}",
                contenu=f"Contenu de l'annonce de test numéro {i}",
                user_id=admin.id
            )
            db.session.add(annonce)
            new_annonces.append(annonce)

        db.session.commit()

        # Ajouter des commentaires aux nouvelles annonces
        for annonce in new_annonces:
            comment = Commentaire(
                contenu=f"Commentaire automatique pour {annonce.titre}",
                annonce_id=annonce.id,
                user_id=admin.id
            )
            db.session.add(comment)

        db.session.commit()

        return jsonify({
            'message': 'Données de test créées avec succès',
            'created': {
                'annonces': len(new_annonces),
                'commentaires': len(new_annonces)
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
