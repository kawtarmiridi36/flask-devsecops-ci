from app import create_app
from app.extensions import db
from app.models import User, Annonce, Commentaire

app = create_app()

with app.app_context():
    print("🗃️  Création des tables de la base de données...")
    
    # Créer toutes les tables
    db.create_all()
    
    # Vérifier
    user_count = User.query.count()
    annonce_count = Annonce.query.count()
    comment_count = Commentaire.query.count()
    
    print(f"✅ Tables créées avec succès!")
    print(f"📊 Stats: Users={user_count}, Annonces={annonce_count}, Commentaires={comment_count}")
    
    # Optionnel: Créer un utilisateur admin de test
    if user_count == 0:
        from app.models import User
        admin = User(username='admin', email='admin@example.com', role='admin')
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print("👤 Utilisateur admin créé: admin / admin123")
