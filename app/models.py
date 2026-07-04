from datetime import datetime, date
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db, login_manager
from google.cloud import firestore

# --- HELPER UTILITY: Estrazione DB Globale ---
# db è il firestore client inizializzato in extensions.py

# ── User ────────────────────────────────────────────────────────────────────
class User(UserMixin):
    collection_name = 'users'

    def __init__(self, uid, username, password_hash, role='capitano', team_id=None):
        self.id = uid  # UserMixin requires an 'id' property
        self.username = username
        self.password_hash = password_hash
        self.role = role
        self.team_id = team_id

    @staticmethod
    def create(username, password, role='capitano', team_id=None):
        user_data = {
            'username': username,
            'password_hash': generate_password_hash(password),
            'role': role,
            'team_id': team_id
        }
        # Verifica unicità username in query
        if User.get_by_username(username):
            raise ValueError("Username already exists")
        
        _, doc_ref = db.collection(User.collection_name).add(user_data)
        return doc_ref.id

    @staticmethod
    def get_by_id(uid):
        if not db: return None
        doc = db.collection(User.collection_name).document(uid).get()
        if doc.exists:
            d = doc.to_dict()
            return User(uid=doc.id, username=d.get('username'), password_hash=d.get('password_hash'),
                        role=d.get('role'), team_id=d.get('team_id'))
        return None

    @staticmethod
    def get_by_username(username):
        if not db: return None
        docs = db.collection(User.collection_name).where('username', '==', username).limit(1).stream()
        for doc in docs:
            d = doc.to_dict()
            return User(uid=doc.id, username=d.get('username'), password_hash=d.get('password_hash'),
                        role=d.get('role'), team_id=d.get('team_id'))
        return None

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username} [{self.role}]>'

@login_manager.user_loader
def load_user(user_id):
    return User.get_by_id(user_id)


# ── Team ────────────────────────────────────────────────────────────────────
class Team:
    collection_name = 'teams'

    @staticmethod
    def create(name, group=None, logo_url=''):
        team_data = {
            'name': name,
            'group': group,
            'logo_url': logo_url,
            'roster': []  # Lista di dizionari invece di una tabella separata RosterPlayer
        }
        # In Firebase possiamo annidare i roster_players direttamente qui come array di mappe/dict
        _, doc_ref = db.collection(Team.collection_name).add(team_data)
        return doc_ref.id

    @staticmethod
    def get_by_id(uid):
        doc = db.collection(Team.collection_name).document(uid).get()
        if doc.exists:
            d = doc.to_dict()
            d['id'] = doc.id
            return d
        return None

    @staticmethod
    def get_all():
        docs = db.collection(Team.collection_name).stream()
        return [{**doc.to_dict(), 'id': doc.id} for doc in docs]

    @staticmethod
    def get_by_group(group_name):
        docs = db.collection(Team.collection_name).where('group', '==', group_name).stream()
        return [{**doc.to_dict(), 'id': doc.id} for doc in docs]

    @staticmethod
    def add_player_to_roster(team_id, player_data):
        """player_data = {'nome': '...', 'cognome': '...', 'scadenza_visita_medica': 'YYYY-MM-DD', 'file_visita': '...'}"""
        team_ref = db.collection(Team.collection_name).document(team_id)
        # Firebase ArrayUnion per appendere alla lista senza sovrascrivere il resto
        team_ref.update({
            'roster': firestore.ArrayUnion([player_data])
        })

    @staticmethod
    def update_coppa_chiosco_points(team_id, delta):
        """Incrementa (delta=+1) o decrementa (delta=-1) i punti Coppa Chiosco."""
        db.collection(Team.collection_name).document(team_id).update({
            'coppa_chiosco_points': firestore.Increment(delta)
        })


# ── Match ───────────────────────────────────────────────────────────────────
class Match:
    collection_name = 'matches'

    @staticmethod
    def create(home_team_id, away_team_id, group=None, phase='group'):
        match_data = {
            'home_team_id': home_team_id,
            'away_team_id': away_team_id,
            'home_score': 0,
            'away_score': 0,
            'phase': phase,
            'group': group,
            'played': False,
            'live': False,
            'match_date': None,
            'match_time': None,
            'man_of_match': None,
            'goals': []  # Anche qui annidiamo i goal direttamente nel match (lista di dizionari)
        }
        _, doc_ref = db.collection(Match.collection_name).add(match_data)
        return doc_ref.id

    @staticmethod
    def get_all():
        docs = db.collection(Match.collection_name).stream()
        return [{**doc.to_dict(), 'id': doc.id} for doc in docs]

    @staticmethod
    def get_by_group(group_name):
        docs = db.collection(Match.collection_name).where('group', '==', group_name).stream()
        return [{**doc.to_dict(), 'id': doc.id} for doc in docs]

    @staticmethod
    def get_by_id(uid):
        doc = db.collection(Match.collection_name).document(uid).get()
        if doc.exists:
            d = doc.to_dict()
            d['id'] = doc.id
            return d
        return None

    @staticmethod
    def update_score_from_goals(match_id):
        # A differenza del relazionale, i goal sono già nella partita.
        match_data = Match.get_by_id(match_id)
        if not match_data: return
        
        home_score = 0
        away_score = 0
        for goal in match_data.get('goals', []):
            if goal['team_id'] == match_data['home_team_id']:
                home_score += 1
            elif goal['team_id'] == match_data['away_team_id']:
                away_score += 1
                
        db.collection(Match.collection_name).document(match_id).update({
            'home_score': home_score,
            'away_score': away_score,
        })

    @staticmethod
    def add_goal(match_id, team_id, player_name, minute=None, is_own_goal=False):
        goal_data = {
            'team_id': team_id,
            'player_name': player_name,
            'minute': minute,
            'is_own_goal': is_own_goal,
        }
        doc_ref = db.collection(Match.collection_name).document(match_id)
        doc_ref.update({
            'goals': firestore.ArrayUnion([goal_data])
        })
        Match.update_score_from_goals(match_id)

    @staticmethod
    def set_datetime(match_id, date_str, time_str):
        doc_ref = db.collection(Match.collection_name).document(match_id)
        doc_ref.update({
            'match_date': date_str,
            'match_time': time_str
        })

