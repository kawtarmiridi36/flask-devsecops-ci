from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
import logging
from ..extensions import db
from ..models import User

members_bp = Blueprint("members", __name__)

@members_bp.route("/", methods=["GET"])
@login_required
def list_members():
    """Liste tous les membres (admin seulement)"""
    try:
        # Vérifier les permissions admin
        if current_user.role != 'admin':
            logging.warning(f"Unauthorized access attempt to members list by user: {current_user.username}")
            return jsonify({"error": "Admin access required"}), 403
        
        users = User.query.all()
        
        # Journalisation
        logging.info(f"Members list accessed by admin: {current_user.username}")
        
        return jsonify([
            {
                "id": u.id,
                "username": u.username, 
                "email": u.email,
                "role": u.role,
                "date_joined": u.date_joined.isoformat() if u.date_joined else None
            }
            for u in users
        ]), 200
        
    except Exception as e:
        logging.error(f"Error listing members: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@members_bp.route("/<int:user_id>", methods=["GET"])
@login_required
def get_member(user_id):
    """Obtenir les informations d'un membre spécifique"""
    try:
        user = User.query.get_or_404(user_id)
        
        # Vérifier les permissions : utilisateur peut voir son propre profil, admin peut voir tout
        if current_user.id != user_id and current_user.role != 'admin':
            logging.warning(f"Unauthorized access attempt to user {user_id} by user: {current_user.username}")
            return jsonify({"error": "Access denied"}), 403
        
        return jsonify({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "date_joined": user.date_joined.isoformat() if user.date_joined else None
        }), 200
        
    except Exception as e:
        logging.error(f"Error getting member {user_id}: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@members_bp.route("/<int:user_id>", methods=["PUT"])
@login_required
def update_member(user_id):
    """Modifier un membre"""
    try:
        user = User.query.get_or_404(user_id)
        data = request.get_json()
        
        # Vérifier les permissions
        if current_user.id != user_id and current_user.role != 'admin':
            logging.warning(f"Unauthorized update attempt on user {user_id} by user: {current_user.username}")
            return jsonify({"error": "Access denied"}), 403
        
        # Validation des données
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Mise à jour des champs avec validation
        updates = {}
        
        if 'username' in data and data['username']:
            if len(data['username']) < 3:
                return jsonify({"error": "Username must be at least 3 characters"}), 400
            # Vérifier si le username est déjà pris
            existing_user = User.query.filter_by(username=data['username']).first()
            if existing_user and existing_user.id != user_id:
                return jsonify({"error": "Username already taken"}), 409
            user.username = data['username']
            updates['username'] = data['username']
        
        if 'email' in data and data['email']:
            # Importer la validation d'email depuis auth
            from ..auth.routes import validate_email
            if not validate_email(data['email']):
                return jsonify({"error": "Invalid email format"}), 400
            # Vérifier si l'email est déjà pris
            existing_user = User.query.filter_by(email=data['email']).first()
            if existing_user and existing_user.id != user_id:
                return jsonify({"error": "Email already taken"}), 409
            user.email = data['email']
            updates['email'] = data['email']
        
        # Seul un admin peut changer le rôle
        if 'role' in data and current_user.role == 'admin':
            if data['role'] not in ['admin', 'membre']:
                return jsonify({"error": "Invalid role"}), 400
            user.role = data['role']
            updates['role'] = data['role']
        elif 'role' in data and current_user.role != 'admin':
            return jsonify({"error": "Only admin can change roles"}), 403
        
        db.session.commit()
        
        # Journalisation
        logging.info(f"User {user_id} updated by {current_user.username}. Changes: {updates}")
        
        return jsonify({
            "message": "User updated successfully",
            "updates": updates
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error updating member {user_id}: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@members_bp.route("/<int:user_id>", methods=["DELETE"])
@login_required
def delete_member(user_id):
    """Supprimer un membre (admin seulement)"""
    try:
        # Vérifier les permissions admin
        if current_user.role != 'admin':
            logging.warning(f"Unauthorized delete attempt on user {user_id} by user: {current_user.username}")
            return jsonify({"error": "Admin access required"}), 403
        
        user = User.query.get_or_404(user_id)
        
        # Empêcher l'auto-suppression
        if user.id == current_user.id:
            return jsonify({"error": "Cannot delete your own account"}), 400
        
        # Sauvegarder les infos pour le log
        username = user.username
        
        db.session.delete(user)
        db.session.commit()
        
        # Journalisation
        logging.info(f"User {username} (ID: {user_id}) deleted by admin: {current_user.username}")
        
        return jsonify({"message": "User deleted successfully"}), 200
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error deleting member {user_id}: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500