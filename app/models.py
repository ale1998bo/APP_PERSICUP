from datetime import datetime, date
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db, login_manager


# ── User ────────────────────────────────────────────────────────────────────
class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='giocatore')  # admin | organizzatore | capitano | giocatore
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id'), nullable=True)

    team = db.relationship('Team', backref=db.backref('players', lazy='dynamic'))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username} [{self.role}]>'


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


# ── Team ────────────────────────────────────────────────────────────────────
class Team(db.Model):
    __tablename__ = 'teams'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    group = db.Column(db.String(1), nullable=False)  # A | B | C | D
    logo_url = db.Column(db.String(256), default='')

    roster = db.relationship('RosterPlayer', backref='team', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Team {self.name} (Group {self.group})>'


# ── Match ───────────────────────────────────────────────────────────────────
class Match(db.Model):
    __tablename__ = 'matches'

    id = db.Column(db.Integer, primary_key=True)
    home_team_id = db.Column(db.Integer, db.ForeignKey('teams.id'), nullable=False)
    away_team_id = db.Column(db.Integer, db.ForeignKey('teams.id'), nullable=False)
    home_score = db.Column(db.Integer, nullable=True, default=0)
    away_score = db.Column(db.Integer, nullable=True, default=0)
    phase = db.Column(db.String(20), nullable=False, default='group')  # group | quarter | semi | final
    group = db.Column(db.String(1), nullable=True)  # A-D for group phase, None for knockouts
    played = db.Column(db.Boolean, default=False)
    match_date = db.Column(db.DateTime, default=datetime.utcnow)
    man_of_match = db.Column(db.String(100), nullable=True)  # MVP name

    home_team = db.relationship('Team', foreign_keys=[home_team_id], backref='home_matches')
    away_team = db.relationship('Team', foreign_keys=[away_team_id], backref='away_matches')
    goals = db.relationship('Goal', backref='match', lazy='dynamic', cascade='all, delete-orphan',
                            order_by='Goal.minute')

    def recalc_score(self):
        """Recalculate score from goals."""
        self.home_score = Goal.query.filter_by(match_id=self.id, team_id=self.home_team_id).count()
        self.away_score = Goal.query.filter_by(match_id=self.id, team_id=self.away_team_id).count()
        self.played = True

    def __repr__(self):
        if self.played:
            return f'<Match {self.home_team.name} {self.home_score}-{self.away_score} {self.away_team.name}>'
        return f'<Match {self.home_team.name} vs {self.away_team.name} ({self.phase})>'


# ── Goal (scorer) ──────────────────────────────────────────────────────────
class Goal(db.Model):
    __tablename__ = 'goals'

    id = db.Column(db.Integer, primary_key=True)
    match_id = db.Column(db.Integer, db.ForeignKey('matches.id'), nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id'), nullable=False)
    player_name = db.Column(db.String(100), nullable=False)
    minute = db.Column(db.Integer, nullable=True)

    team = db.relationship('Team')

    def __repr__(self):
        m = f"{self.minute}'" if self.minute else ''
        return f'<Goal {self.player_name} {m} ({self.team.name})>'


# ── Roster Player (managed by captain) ──────────────────────────────────────
class RosterPlayer(db.Model):
    __tablename__ = 'roster_players'

    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id'), nullable=False)
    nome = db.Column(db.String(100), nullable=False)
    cognome = db.Column(db.String(100), nullable=False)
    scadenza_visita_medica = db.Column(db.Date, nullable=True)
    file_visita_medica = db.Column(db.String(256), nullable=True)  # filename in uploads/

    @property
    def visita_scaduta(self):
        if not self.scadenza_visita_medica:
            return True
        return self.scadenza_visita_medica < date.today()

    def __repr__(self):
        return f'<RosterPlayer {self.nome} {self.cognome} ({self.team.name})>'

