from app import create_app, db
from app.models import User, Annonce, Commentaire

app = create_app()

with app.app_context():
    print("🔄 Création des données de test...")

    # S'assurer que les tables existent
    db.create_all()

    # Récupérer un utilisateur existant (par ex. admin créé dans init_db.py)
    user = User.query.filter_by(username="admin").first()

    # Si pour une raison quelconque il n'existe pas, on en crée un
    if not user:
        print("⚠️ Utilisateur admin introuvable, création d'un admin de test...")
        user = User(
            username="admin",
            email="admin@example.com",
            role="admin"
        )
        user.set_password("admin123")
        db.session.add(user)
        db.session.commit()
        print("✅ Utilisateur admin créé.")

    # Ne pas dupliquer les données si elles existent déjà
    if Annonce.query.count() == 0:
        print("📝 Création des annonces de test...")

        annonce1 = Annonce(
            titre="Première annonce",
            contenu="Ceci est une annonce de test pour l'application du club DevSecOps.",
            user_id=user.id
        )

        annonce2 = Annonce(
            titre="Annonce importante",
            contenu="Une autre annonce pour tester l'affichage et les commentaires.",
            user_id=user.id
        )

        db.session.add_all([annonce1, annonce2])
        db.session.commit()
        print("✅ Annonces créées.")

        print("💬 Création des commentaires de test...")

        comment1 = Commentaire(
            contenu="Super annonce ! 👏",
            annonce_id=annonce1.id,
            user_id=user.id
        )

        comment2 = Commentaire(
            contenu="Très intéressant, merci pour l'info.",
            annonce_id=annonce1.id,
            user_id=user.id
        )

        comment3 = Commentaire(
            contenu="On va pouvoir utiliser ça pour nos réunions.",
            annonce_id=annonce2.id,
            user_id=user.id
        )

        db.session.add_all([comment1, comment2, comment3])
        db.session.commit()
        print("✅ Commentaires créés.")
    else:
        print("ℹ️ Des annonces existent déjà, aucune donnée de test ajoutée.")

    print("🎉 Données de test prêtes !")
