import os
import json
import firebase_admin
from firebase_admin import credentials, firestore
from flask_login import LoginManager
from werkzeug.local import LocalProxy

def get_db():
    return firestore.client()

db = LocalProxy(get_db)

def init_firebase(app):
    if firebase_admin._apps:
        return
    cred_json = os.environ.get('FIREBASE_CREDENTIALS')
    if cred_json:
        cred = credentials.Certificate(json.loads(cred_json))
    elif os.path.exists('firebase_credentials.json'):
        cred = credentials.Certificate('firebase_credentials.json')
    else:
        # Cloud Run / GCP: usa Application Default Credentials
        cred = None
    options = {'projectId': app.config.get('FIREBASE_PROJECT_ID')}
    firebase_admin.initialize_app(cred, options)

login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Effettua il login per accedere a questa pagina.'
login_manager.login_message_category = 'warning'
