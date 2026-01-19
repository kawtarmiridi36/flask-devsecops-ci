from .extensions import db, bcrypt
from flask_login import UserMixin
from datetime import datetime

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200))
    role = db.Column(db.String(20), default="membre")
    date_joined = db.Column(db.DateTime, default=datetime.utcnow)  # NOUVEAU
    
    # RELATIONS (NOUVEAU)
    annonces = db.relationship('Annonce', backref='auteur', lazy=True, cascade="all, delete-orphan")
    commentaires = db.relationship('Commentaire', backref='auteur', lazy=True, cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode()

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)
    
    def __repr__(self):  # NOUVEAU - pour le débogage
        return f'<User {self.username}>'

class Annonce(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titre = db.Column(db.String(100), nullable=False)
    contenu = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # NOUVEAU - lien utilisateur
    
    # RELATION (NOUVEAU)
    commentaires = db.relationship('Commentaire', backref='annonce', lazy=True, cascade="all, delete-orphan")
    
    def __repr__(self):  # NOUVEAU - pour le débogage
        return f'<Annonce {self.titre}>'

class Commentaire(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    contenu = db.Column(db.String(500), nullable=False)  # AUGMENTÉ de 200 à 500
    date = db.Column(db.DateTime, default=datetime.utcnow)
    annonce_id = db.Column(db.Integer, db.ForeignKey('annonce.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # NOUVEAU - lien utilisateur
    
    def __repr__(self):  # NOUVEAU - pour le débogage
        return f'<Commentaire {self.id}>'
