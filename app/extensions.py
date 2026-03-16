import firebase_admin
from firebase_admin import credentials, firestore
from flask_login import LoginManager
from werkzeug.local import LocalProxy

def get_db():
    return firestore.client()

db = LocalProxy(get_db)

def init_firebase(app):
    # Inizializza l'app Firebase usando le credenziali in root directory
    cred = credentials.Certificate("firebase_credentials.json")
    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred)

login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Effettua il login per accedere a questa pagina.'
login_manager.login_message_category = 'warning'
