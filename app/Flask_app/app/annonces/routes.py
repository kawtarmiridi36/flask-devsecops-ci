from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
import logging
from datetime import datetime
from ..extensions import db
from ..models import Annonce, Commentaire

annonces_bp = Blueprint("annonces", __name__)

# 🔧 ADD METRICS IMPORTS AT THE TOP
try:
    from ..metrics import ANNOUNCEMENT_COUNT
    METRICS_ENABLED = True
except ImportError:
    METRICS_ENABLED = False
    logging.warning("Prometheus metrics not available - skipping metrics tracking")

@annonces_bp.route("/", methods=["POST"])
@login_required
def create_annonce():
    """Créer une annonce avec validation"""
    try:
        data = request.get_json()
        
        # Validation des champs requis
        if not data or not all(k in data for k in ['titre', 'contenu']):
            return jsonify({"error": "Title and content are required"}), 400
        
        # Validation du titre
        if len(data["titre"]) < 5:
            return jsonify({"error": "Title must be at least 5 characters"}), 400
        
        # Validation du contenu
        if len(data["contenu"]) < 10:
            return jsonify({"error": "Content must be at least 10 characters"}), 400
        
        # Création de l'annonce avec l'utilisateur connecté
        annonce = Annonce(
            titre=data["titre"], 
            contenu=data["contenu"],
            user_id=current_user.id  # Lier à l'utilisateur connecté
        )
        db.session.add(annonce)
        db.session.commit()
        
        # 🔧 METRICS: Increment announcement counter
        if METRICS_ENABLED:
            try:
                ANNOUNCEMENT_COUNT.inc()
                logging.info(f"✅ Metrics: Annonce counter incremented for new announcement by {current_user.username}")
            except Exception as metrics_error:
                logging.warning(f"⚠️  Could not increment metrics: {metrics_error}")
        
        # Journalisation
        logging.info(f"Annonce created by {current_user.username}: {annonce.titre}")
        
        return jsonify({
            "message": "Annonce créée avec succès",
            "annonce": {
                "id": annonce.id,
                "titre": annonce.titre,
                "contenu": annonce.contenu,
                "date": annonce.date.isoformat(),
                "user_id": annonce.user_id
            },
            "metrics": {
                "announcement_count_incremented": METRICS_ENABLED
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error creating annonce: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@annonces_bp.route("/", methods=["GET"])
def list_annonces():
    """Lister toutes les annonces avec leurs commentaires"""
    try:
        annonces = Annonce.query.order_by(Annonce.date.desc()).all()
        
        result = []
        for annonce in annonces:
            commentaires = Commentaire.query.filter_by(annonce_id=annonce.id).all()
            result.append({
                "id": annonce.id,
                "titre": annonce.titre,
                "contenu": annonce.contenu,
                "date": annonce.date.isoformat(),
                "user_id": annonce.user_id,
                "auteur": annonce.auteur.username if annonce.auteur else "Unknown",  # NOUVEAU
                "commentaires_count": len(commentaires),
                "commentaires": [{
                    "id": c.id,
                    "contenu": c.contenu,
                    "date": c.date.isoformat(),
                    "user_id": c.user_id,
                    "auteur": c.auteur.username if c.auteur else "Unknown"  # NOUVEAU
                } for c in commentaires]
            })
        
        # 🔧 METRICS: Update active users gauge if we had that info
        # You could add: update_active_users(len(result)) if tracking active content
        
        return jsonify(result), 200
        
    except Exception as e:
        logging.error(f"Error listing annonces: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@annonces_bp.route("/<int:annonce_id>", methods=["GET"])
def get_annonce(annonce_id):
    """Obtenir une annonce spécifique avec ses commentaires"""
    try:
        annonce = Annonce.query.get_or_404(annonce_id)
        commentaires = Commentaire.query.filter_by(annonce_id=annonce_id).order_by(Commentaire.date.asc()).all()
        
        return jsonify({
            "id": annonce.id,
            "titre": annonce.titre,
            "contenu": annonce.contenu,
            "date": annonce.date.isoformat(),
            "user_id": annonce.user_id,
            "auteur": annonce.auteur.username if annonce.auteur else "Unknown",
            "commentaires": [{
                "id": c.id,
                "contenu": c.contenu,
                "date": c.date.isoformat(),
                "user_id": c.user_id,
                "auteur": c.auteur.username if c.auteur else "Unknown"
            } for c in commentaires]
        }), 200
        
    except Exception as e:
        logging.error(f"Error getting annonce {annonce_id}: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@annonces_bp.route("/<int:annonce_id>", methods=["PUT"])
@login_required
def update_annonce(annonce_id):
    """Modifier une annonce"""
    try:
        annonce = Annonce.query.get_or_404(annonce_id)
        data = request.get_json()
        
        # Vérifier les permissions : propriétaire ou admin
        if annonce.user_id != current_user.id and current_user.role != 'admin':
            logging.warning(f"Unauthorized update attempt on annonce {annonce_id} by user: {current_user.username}")
            return jsonify({"error": "Access denied"}), 403
        
        # Validation des données
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        updates = {}
        
        if 'titre' in data and data['titre']:
            if len(data['titre']) < 5:
                return jsonify({"error": "Title must be at least 5 characters"}), 400
            annonce.titre = data['titre']
            updates['titre'] = data['titre']
        
        if 'contenu' in data and data['contenu']:
            if len(data['contenu']) < 10:
                return jsonify({"error": "Content must be at least 10 characters"}), 400
            annonce.contenu = data['contenu']
            updates['contenu'] = data['contenu']
        
        annonce.date = datetime.utcnow()  # Mettre à jour la date de modification
        
        db.session.commit()
        
        # Journalisation
        logging.info(f"Annonce {annonce_id} updated by {current_user.username}. Changes: {updates}")
        
        return jsonify({
            "message": "Annonce modifiée avec succès",
            "updates": updates
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error updating annonce {annonce_id}: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@annonces_bp.route("/<int:annonce_id>", methods=["DELETE"])
@login_required
def delete_annonce(annonce_id):
    """Supprimer une annonce et ses commentaires"""
    try:
        annonce = Annonce.query.get_or_404(annonce_id)
        
        # Vérifier les permissions : propriétaire ou admin
        if annonce.user_id != current_user.id and current_user.role != 'admin':
            logging.warning(f"Unauthorized delete attempt on annonce {annonce_id} by user: {current_user.username}")
            return jsonify({"error": "Access denied"}), 403
        
        # Sauvegarder les infos pour le log
        titre = annonce.titre
        commentaires_count = Commentaire.query.filter_by(annonce_id=annonce_id).count()
        
        # Supprimer les commentaires associés (cascade)
        Commentaire.query.filter_by(annonce_id=annonce_id).delete()
        
        # Supprimer l'annonce
        db.session.delete(annonce)
        db.session.commit()
        
        # 🔧 METRICS: You could add a metric for deletions if needed
        # Example: if METRICS_ENABLED: ANNOUNCEMENT_DELETED_COUNT.inc()
        
        # Journalisation
        logging.info(f"Annonce '{titre}' (ID: {annonce_id}) with {commentaires_count} comments deleted by {current_user.username}")
        
        return jsonify({
            "message": "Annonce et commentaires associés supprimés avec succès",
            "deleted": {
                "annonce": titre,
                "commentaires": commentaires_count
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error deleting annonce {annonce_id}: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@annonces_bp.route("/user/<int:user_id>", methods=["GET"])  # NOUVEAU
def get_user_annonces(user_id):
    """Obtenir toutes les annonces d'un utilisateur spécifique"""
    try:
        annonces = Annonce.query.filter_by(user_id=user_id).order_by(Annonce.date.desc()).all()
        
        return jsonify([{
            "id": a.id,
            "titre": a.titre,
            "contenu": a.contenu,
            "date": a.date.isoformat(),
            "commentaires_count": Commentaire.query.filter_by(annonce_id=a.id).count()
        } for a in annonces]), 200
        
    except Exception as e:
        logging.error(f"Error getting annonces for user {user_id}: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

# 🔧 ADD METRICS ENDPOINT TO THE BLUEPRINT (Optional)
@annonces_bp.route("/metrics-info", methods=["GET"])
def annonces_metrics_info():
    """Information about annonces metrics"""
    return jsonify({
        "service": "annonces",
        "metrics": {
            "available": METRICS_ENABLED,
            "counters": [
                "flask_announcements_total"
            ],
            "endpoints": {
                "global_metrics": "/metrics",
                "create_annonce": "Increments flask_announcements_total"
            }
        }
    })
