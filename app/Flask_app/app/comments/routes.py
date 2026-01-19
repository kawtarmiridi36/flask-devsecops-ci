from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
import logging
from datetime import datetime
from ..extensions import db
from ..models import Commentaire, Annonce

comments_bp = Blueprint("comments", __name__)

@comments_bp.route("/", methods=["POST"])
@login_required
def add_comment():
    """Ajouter un commentaire avec validation"""
    try:
        data = request.get_json()
        
        # Validation des champs requis
        if not data or not all(k in data for k in ['contenu', 'annonce_id']):
            return jsonify({"error": "Content and annonce_id are required"}), 400
        
        # Validation du contenu
        if len(data["contenu"]) < 2:
            return jsonify({"error": "Comment must be at least 2 characters"}), 400
        
        if len(data["contenu"]) > 500:
            return jsonify({"error": "Comment must be less than 500 characters"}), 400
        
        # Vérifier que l'annonce existe
        annonce = Annonce.query.get(data["annonce_id"])
        if not annonce:
            return jsonify({"error": "Annonce not found"}), 404
        
        # Création du commentaire avec l'utilisateur connecté
        comment = Commentaire(
            contenu=data["contenu"],
            annonce_id=data["annonce_id"],
            user_id=current_user.id  # Lier à l'utilisateur connecté
        )
        db.session.add(comment)
        db.session.commit()
        
        # Journalisation
        logging.info(f"Comment added by {current_user.username} on annonce {annonce.id}")
        
        return jsonify({
            "message": "Commentaire ajouté avec succès",
            "comment": {
                "id": comment.id,
                "contenu": comment.contenu,
                "date": comment.date.isoformat(),
                "user_id": comment.user_id,
                "annonce_id": comment.annonce_id,
                "auteur": comment.auteur.username if comment.auteur else "Unknown"
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error adding comment: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@comments_bp.route("/<int:comment_id>", methods=["GET"])
def get_comment(comment_id):
    """Obtenir un commentaire spécifique"""
    try:
        comment = Commentaire.query.get_or_404(comment_id)
        
        return jsonify({
            "id": comment.id,
            "contenu": comment.contenu,
            "date": comment.date.isoformat(),
            "user_id": comment.user_id,
            "annonce_id": comment.annonce_id,
            "auteur": comment.auteur.username if comment.auteur else "Unknown",
            "annonce_titre": comment.annonce.titre if comment.annonce else "Unknown"
        }), 200
        
    except Exception as e:
        logging.error(f"Error getting comment {comment_id}: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@comments_bp.route("/<int:comment_id>", methods=["PUT"])
@login_required
def update_comment(comment_id):
    """Modifier un commentaire"""
    try:
        comment = Commentaire.query.get_or_404(comment_id)
        data = request.get_json()
        
        # Vérifier les permissions : propriétaire ou admin
        if comment.user_id != current_user.id and current_user.role != 'admin':
            logging.warning(f"Unauthorized update attempt on comment {comment_id} by user: {current_user.username}")
            return jsonify({"error": "Access denied"}), 403
        
        # Validation des données
        if not data or not data.get('contenu'):
            return jsonify({"error": "Content is required"}), 400
        
        # Validation du contenu
        if len(data['contenu']) < 2:
            return jsonify({"error": "Comment must be at least 2 characters"}), 400
        
        if len(data['contenu']) > 500:
            return jsonify({"error": "Comment must be less than 500 characters"}), 400
        
        # Mise à jour du commentaire
        old_content = comment.contenu
        comment.contenu = data['contenu']
        comment.date = datetime.utcnow()  # Mettre à jour la date
        
        db.session.commit()
        
        # Journalisation
        logging.info(f"Comment {comment_id} updated by {current_user.username}. From: '{old_content}' To: '{data['contenu']}'")
        
        return jsonify({
            "message": "Commentaire modifié avec succès",
            "comment": {
                "id": comment.id,
                "contenu": comment.contenu,
                "date": comment.date.isoformat()
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error updating comment {comment_id}: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@comments_bp.route("/<int:comment_id>", methods=["DELETE"])
@login_required
def delete_comment(comment_id):
    """Supprimer un commentaire"""
    try:
        comment = Commentaire.query.get_or_404(comment_id)
        
        # Vérifier les permissions : propriétaire ou admin
        if comment.user_id != current_user.id and current_user.role != 'admin':
            logging.warning(f"Unauthorized delete attempt on comment {comment_id} by user: {current_user.username}")
            return jsonify({"error": "Access denied"}), 403
        
        # Sauvegarder les infos pour le log
        annonce_id = comment.annonce_id
        auteur = comment.auteur.username if comment.auteur else "Unknown"
        contenu_preview = comment.contenu[:50] + "..." if len(comment.contenu) > 50 else comment.contenu
        
        # Supprimer le commentaire
        db.session.delete(comment)
        db.session.commit()
        
        # Journalisation
        logging.info(f"Comment by {auteur} on annonce {annonce_id} deleted by {current_user.username}. Content: '{contenu_preview}'")
        
        return jsonify({
            "message": "Commentaire supprimé avec succès",
            "deleted": {
                "comment_id": comment_id,
                "annonce_id": annonce_id
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error deleting comment {comment_id}: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@comments_bp.route("/annonce/<int:annonce_id>", methods=["GET"])
def get_annonce_comments(annonce_id):
    """Obtenir tous les commentaires d'une annonce spécifique"""
    try:
        # Vérifier que l'annonce existe
        annonce = Annonce.query.get(annonce_id)
        if not annonce:
            return jsonify({"error": "Annonce not found"}), 404
        
        comments = Commentaire.query.filter_by(annonce_id=annonce_id).order_by(Commentaire.date.asc()).all()
        
        return jsonify([{
            "id": c.id,
            "contenu": c.contenu,
            "date": c.date.isoformat(),
            "user_id": c.user_id,
            "auteur": c.auteur.username if c.auteur else "Unknown",
            "can_edit": current_user.is_authenticated and (c.user_id == current_user.id or current_user.role == 'admin')
        } for c in comments]), 200
        
    except Exception as e:
        logging.error(f"Error getting comments for annonce {annonce_id}: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@comments_bp.route("/user/<int:user_id>", methods=["GET"])
def get_user_comments(user_id):
    """Obtenir tous les commentaires d'un utilisateur spécifique"""
    try:
        comments = Commentaire.query.filter_by(user_id=user_id).order_by(Commentaire.date.desc()).all()
        
        return jsonify([{
            "id": c.id,
            "contenu": c.contenu,
            "date": c.date.isoformat(),
            "annonce_id": c.annonce_id,
            "annonce_titre": c.annonce.titre if c.annonce else "Unknown"
        } for c in comments]), 200
        
    except Exception as e:
        logging.error(f"Error getting comments for user {user_id}: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@comments_bp.route("/moderation/pending", methods=["GET"])  # NOUVEAU - Système de modération
@login_required
def get_pending_comments():
    """Obtenir les commentaires nécessitant une modération (admin seulement)"""
    try:
        # Vérifier les permissions admin
        if current_user.role != 'admin':
            return jsonify({"error": "Admin access required"}), 403
        
        # Ici vous pourriez ajouter une logique de modération
        # Pour l'instant, retourne tous les commentaires récents
        recent_comments = Commentaire.query.order_by(Commentaire.date.desc()).limit(50).all()
        
        return jsonify([{
            "id": c.id,
            "contenu": c.contenu,
            "date": c.date.isoformat(),
            "user_id": c.user_id,
            "auteur": c.auteur.username if c.auteur else "Unknown",
            "annonce_titre": c.annonce.titre if c.annonce else "Unknown",
            "annonce_id": c.annonce_id
        } for c in recent_comments]), 200
        
    except Exception as e:
        logging.error(f"Error getting pending comments: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500