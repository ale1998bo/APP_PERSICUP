"""
Reset / crea l'utente admin su Firestore.

Uso:
    python reset_admin.py

Se esiste gia' un utente con username ADMIN_USERNAME ne resetta la password
e forza il ruolo 'admin'. Altrimenti lo crea da zero.
"""

from werkzeug.security import generate_password_hash

from app import create_app
from app.extensions import db
from app.models import User

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin"
ADMIN_ROLE = "admin"


def reset_admin():
    app = create_app()
    with app.app_context():
        print("Connesso a Firestore...")

        existing = User.get_by_username(ADMIN_USERNAME)
        new_hash = generate_password_hash(ADMIN_PASSWORD)

        if existing:
            db.collection(User.collection_name).document(existing.id).update({
                "password_hash": new_hash,
                "role": ADMIN_ROLE,
            })
            print(f"[OK] Password resettata per '{ADMIN_USERNAME}' (id={existing.id}).")
        else:
            _, doc_ref = db.collection(User.collection_name).add({
                "username": ADMIN_USERNAME,
                "password_hash": new_hash,
                "role": ADMIN_ROLE,
                "team_id": None,
            })
            print(f"[OK] Utente '{ADMIN_USERNAME}' creato (id={doc_ref.id}).")

        print(f"\nCredenziali: {ADMIN_USERNAME} / {ADMIN_PASSWORD}")
        print("Ora puoi fare login su /auth/login.")


if __name__ == "__main__":
    reset_admin()
