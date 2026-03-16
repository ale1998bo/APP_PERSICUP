from app import create_app
from app.models import User

app = create_app()

with app.app_context():
    try:
        # Check if admin already exists
        if User.get_by_username('admin'):
            print("L'utente admin esiste già!")
        else:
            doc_id = User.create(username='admin', password='admin_password', role='admin')
            print(f"Utente admin creato con successo! ID: {doc_id}")
            print("Username: admin")
            print("Password: admin_password")
    except Exception as e:
        print(f"Errore durante la creazione: {e}")
