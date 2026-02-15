# -*- coding: utf-8 -*-
"""
Seed script — populates the database with:
  • 1 admin user (admin / admin)
  • 1 organizer user (org / org)
  • 2 captain users linked to teams
  • 16 teams in 4 groups (A-D)
  • All group-stage matches (6 per group = 24 total)
  • Roster players for Roma and Juventus

Usage:
  python seed.py
"""

from datetime import date, timedelta
from app import create_app
from app.extensions import db
from app.models import User, Team, Match, RosterPlayer

app = create_app('dev')

TEAMS = {
    'A': ['Roma', 'Milan', 'Lazio', 'Napoli'],
    'B': ['Juventus', 'Inter', 'Atalanta', 'Fiorentina'],
    'C': ['Torino', 'Bologna', 'Sassuolo', 'Cagliari'],
    'D': ['Sampdoria', 'Genoa', 'Udinese', 'Verona'],
}

ROSTERS = {
    'Roma': [
        ('Francesco', 'Totti'),
        ('Daniele', 'De Rossi'),
        ('Alessandro', 'Florenzi'),
        ('Edin', 'Dzeko'),
        ('Lorenzo', 'Pellegrini'),
    ],
    'Juventus': [
        ('Alessandro', 'Del Piero'),
        ('Gianluigi', 'Buffon'),
        ('Andrea', 'Pirlo'),
        ('Paulo', 'Dybala'),
        ('Federico', 'Chiesa'),
    ],
}


def seed():
    with app.app_context():
        db.drop_all()
        db.create_all()
        print('[OK] Database resettato.')

        # ── Teams ───────────────────────────────────────────────────
        team_objs = {}
        for group, names in TEAMS.items():
            for name in names:
                t = Team(name=name, group=group)
                db.session.add(t)
                team_objs[name] = t

        db.session.flush()  # assign IDs

        # ── Users ───────────────────────────────────────────────────
        admin = User(username='admin', role='admin')
        admin.set_password('admin')
        db.session.add(admin)

        org = User(username='org', role='organizzatore')
        org.set_password('org')
        db.session.add(org)

        cap_roma = User(username='caproma', role='capitano', team_id=team_objs['Roma'].id)
        cap_roma.set_password('caproma')
        db.session.add(cap_roma)

        cap_juve = User(username='capjuve', role='capitano', team_id=team_objs['Juventus'].id)
        cap_juve.set_password('capjuve')
        db.session.add(cap_juve)

        # ── Roster Players ──────────────────────────────────────────
        future = date.today() + timedelta(days=180)
        for team_name, players in ROSTERS.items():
            for nome, cognome in players:
                rp = RosterPlayer(
                    team_id=team_objs[team_name].id,
                    nome=nome,
                    cognome=cognome,
                    scadenza_visita_medica=future,
                )
                db.session.add(rp)

        # ── Group Matches (round-robin: 6 matches per group) ───────
        match_count = 0
        for group, names in TEAMS.items():
            teams_in_group = [team_objs[n] for n in names]
            for i in range(len(teams_in_group)):
                for j in range(i + 1, len(teams_in_group)):
                    m = Match(
                        home_team_id=teams_in_group[i].id,
                        away_team_id=teams_in_group[j].id,
                        phase='group',
                        group=group,
                    )
                    db.session.add(m)
                    match_count += 1

        db.session.commit()

        print(f'[OK] Creati {len(team_objs)} squadre in {len(TEAMS)} gironi.')
        print(f'[OK] Creati {match_count} partite dei gironi.')
        print(f'[OK] Rose: Roma ({len(ROSTERS["Roma"])} giocatori), Juventus ({len(ROSTERS["Juventus"])} giocatori)')
        print(f'[OK] Utenti: admin/admin, org/org, caproma/caproma, capjuve/capjuve')
        print('[OK] Seed completato! Esegui: python run.py')


if __name__ == '__main__':
    seed()
