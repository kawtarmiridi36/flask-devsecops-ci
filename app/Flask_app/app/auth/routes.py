from flask import Blueprint, request, jsonify
import re
import logging
from ..extensions import db
from ..models import User
from flask_login import login_user, logout_user, current_user

auth_bp = Blueprint("auth", __name__)

# Fonctions de validation (NOUVEAU)
def validate_email(email):
    """Valide le format d'email"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    """Valide la force du mot de passe"""
    return len(password) >= 6  # Au moins 6 caractères

def validate_username(username):
    """Valide le format du username"""
    return len(username) >= 3 and username.isalnum()

@auth_bp.route("/register", methods=["POST"])
def register():
    """Inscription d'un nouvel utilisateur avec validation"""
    try:
        data = request.get_json()
        
        # Validation des champs requis
        if not data or not all(k in data for k in ['username', 'email', 'password']):
            return jsonify({"error": "Username, email and password are required"}), 400
        
        # Validation du username
        if not validate_username(data["username"]):
            return jsonify({"error": "Username must be at least 3 alphanumeric characters"}), 400
        
        # Validation de l'email
        if not validate_email(data["email"]):
            return jsonify({"error": "Invalid email format"}), 400
        
        # Validation du mot de passe
        if not validate_password(data["password"]):
            return jsonify({"error": "Password must be at least 6 characters"}), 400
        
        # Vérifier si l'utilisateur existe déjà
        if User.query.filter_by(username=data["username"]).first():
            return jsonify({"error": "Username already exists"}), 409
        
        if User.query.filter_by(email=data["email"]).first():
            return jsonify({"error": "Email already exists"}), 409
        
        # Création de l'utilisateur
        user = User(username=data["username"], email=data["email"])
        user.set_password(data["password"])
        db.session.add(user)
        db.session.commit()
        
        # Journalisation (NOUVEAU)
        logging.info(f"New user registered: {user.username} ({user.email})")
        
        return jsonify({
            "message": "User created successfully",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Registration error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@auth_bp.route("/login", methods=["POST"])
def login():
    """Connexion utilisateur avec validation"""
    try:
        data = request.get_json()
        
        # Validation des champs requis
        if not data or not all(k in data for k in ['username', 'password']):
            return jsonify({"error": "Username and password are required"}), 400
        
        # Recherche de l'utilisateur
        user = User.query.filter_by(username=data["username"]).first()
        
        if user and user.check_password(data["password"]):
            login_user(user)
            
            # Journalisation (NOUVEAU)
            logging.info(f"User logged in: {user.username}")
            
            return jsonify({
                "message": "Logged in successfully",
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "role": user.role
                }
            }), 200
        
        # Journalisation des tentatives échouées (NOUVEAU)
        logging.warning(f"Failed login attempt for username: {data['username']}")
        return jsonify({"error": "Invalid credentials"}), 401
        
    except Exception as e:
        logging.error(f"Login error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@auth_bp.route("/logout", methods=["POST"])
def logout():
    """Déconnexion utilisateur"""
    if current_user.is_authenticated:
        username = current_user.username
        logout_user()
        logging.info(f"User logged out: {username}")  # NOUVEAU
        return jsonify({"message": "Logged out successfully"}), 200
    else:
        return jsonify({"error": "No user is logged in"}), 400

@auth_bp.route("/me", methods=["GET"])  # NOUVEAU
def get_current_user():
    """Obtenir les informations de l'utilisateur connecté"""
    if current_user.is_authenticated:
        return jsonify({
            "id": current_user.id,
            "username": current_user.username,
            "email": current_user.email,
            "role": current_user.role
        }), 200
    else:
        return jsonify({"error": "Not authenticated"}), 401