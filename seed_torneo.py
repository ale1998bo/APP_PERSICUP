# -*- coding: utf-8 -*-
"""
Seed torneo reale — Coppa Chiosco 2026
  - Pulisce le collezioni 'teams' e 'matches' su Firestore
  - Crea le 16 squadre reali divise in 4 gironi (A, B, C, D)
  - Crea le 24 partite con calendario reale

Giornate:
  G1 — Lunedì   22 giugno 2026
  G2 — Martedì  23 giugno 2026
  G3 — Giovedì  25 giugno 2026
  G4 — Venerdì  26 giugno 2026

Uso:
    python seed_torneo.py
    python seed_torneo.py --no-wipe   # crea senza cancellare prima
"""

import sys
from app import create_app
from app.extensions import db
from app.models import Team, Match

# ── Squadre per girone ──────────────────────────────────────────────────────
SQUADRE_PER_GIRONE = {
    'A': ['Bartolini SRL', 'Loco Café', 'Alpha Wolf', 'Real Tempo AMS'],
    'B': ['M&M Parrucchieri', 'Pasca Barber Team', 'Castelli e Tortelli', 'Il Barone Rosso'],
    'C': ['Stabaco', 'Decimacar', 'La Rotonda sul Pane', 'Pizzeria di Palma'],
    'D': ['Ficaroless', 'Old Money', 'Cisanova', 'Pizzeria Mirò'],
}

# ── Calendario: (data, orario, girone, casa, ospite) ────────────────────────
CALENDARIO = [
    # GIORNATA 1 — Lunedì 22 giugno 2026
    ('2026-06-22', '20:00', 'B', 'M&M Parrucchieri',   'Pasca Barber Team'),
    ('2026-06-22', '20:15', 'D', 'Ficaroless',          'Old Money'),
    ('2026-06-22', '21:00', 'A', 'Real Tempo AMS',      'Loco Café'),
    ('2026-06-22', '21:15', 'C', 'Stabaco',             'Pizzeria di Palma'),
    ('2026-06-22', '22:00', 'C', 'Decimacar',           'La Rotonda sul Pane'),
    ('2026-06-22', '22:15', 'D', 'Cisanova',            'Pizzeria Mirò'),
    # GIORNATA 2 — Martedì 23 giugno 2026
    ('2026-06-23', '20:00', 'C', 'Decimacar',           'Pizzeria di Palma'),
    ('2026-06-23', '20:15', 'A', 'Bartolini SRL',       'Loco Café'),
    ('2026-06-23', '21:00', 'D', 'Old Money',           'Cisanova'),
    ('2026-06-23', '21:15', 'A', 'Alpha Wolf',          'Real Tempo AMS'),
    ('2026-06-23', '22:00', 'B', 'Castelli e Tortelli', 'Il Barone Rosso'),
    ('2026-06-23', '22:15', 'C', 'Stabaco',             'La Rotonda sul Pane'),
    # GIORNATA 3 — Giovedì 25 giugno 2026
    ('2026-06-25', '20:00', 'A', 'Alpha Wolf',          'Loco Café'),
    ('2026-06-25', '20:15', 'B', 'M&M Parrucchieri',   'Castelli e Tortelli'),
    ('2026-06-25', '21:00', 'D', 'Ficaroless',          'Cisanova'),
    ('2026-06-25', '21:15', 'B', 'Pasca Barber Team',   'Il Barone Rosso'),
    ('2026-06-25', '22:00', 'D', 'Old Money',           'Pizzeria Mirò'),
    ('2026-06-25', '22:15', 'A', 'Bartolini SRL',       'Real Tempo AMS'),
    # GIORNATA 4 — Venerdì 26 giugno 2026
    ('2026-06-26', '20:00', 'C', 'Stabaco',             'Decimacar'),
    ('2026-06-26', '20:15', 'B', 'Pasca Barber Team',   'Castelli e Tortelli'),
    ('2026-06-26', '21:00', 'D', 'Ficaroless',          'Pizzeria Mirò'),
    ('2026-06-26', '21:15', 'A', 'Bartolini SRL',       'Alpha Wolf'),
    ('2026-06-26', '22:00', 'B', 'M&M Parrucchieri',   'Il Barone Rosso'),
    ('2026-06-26', '22:15', 'C', 'La Rotonda sul Pane', 'Pizzeria di Palma'),
]


# ── Helpers ─────────────────────────────────────────────────────────────────
def wipe_collection(collection_name):
    deleted = 0
    for doc in db.collection(collection_name).stream():
        doc.reference.delete()
        deleted += 1
    return deleted


def seed(wipe=True):
    app = create_app()

    with app.app_context():
        print('Connesso a Firestore.\n')

        # 1. Pulizia (opzionale)
        if wipe:
            n_m = wipe_collection(Match.collection_name)
            n_t = wipe_collection(Team.collection_name)
            print(f'[WIPE] Eliminate {n_t} squadre e {n_m} partite esistenti.\n')

        # 2. Crea squadre e costruisce la mappa nome -> id
        print('Creazione squadre...')
        team_id_by_name = {}
        for girone, squadre in SQUADRE_PER_GIRONE.items():
            for nome in squadre:
                team_data = {
                    'name': nome,
                    'group': girone,
                    'logo_url': '',
                    'roster': [],
                }
                _, ref = db.collection(Team.collection_name).add(team_data)
                team_id_by_name[nome] = ref.id
                print(f'  [{girone}] {nome}  → {ref.id}')

        print(f'\n[OK] {len(team_id_by_name)} squadre create.\n')

        # 3. Crea partite
        print('Creazione partite...')
        giornata_corrente = None
        for data, orario, girone, casa, ospite in CALENDARIO:
            # Stampa intestazione giornata al cambio di data
            if data != giornata_corrente:
                giornata_corrente = data
                print(f'\n  --- {data} ---')

            home_id = team_id_by_name.get(casa)
            away_id = team_id_by_name.get(ospite)

            if not home_id or not away_id:
                print(f'  [ERRORE] Squadra non trovata: "{casa}" o "{ospite}"')
                continue

            match_data = {
                'home_team_id': home_id,
                'away_team_id': away_id,
                'home_score': 0,
                'away_score': 0,
                'phase': 'group',
                'group': girone,
                'played': False,
                'match_date': data,
                'match_time': orario,
                'man_of_match': None,
                'goals': [],
            }
            _, ref = db.collection(Match.collection_name).add(match_data)
            print(f'  {orario} [{girone}]  {casa}  vs  {ospite}')

        print(f'\n[OK] {len(CALENDARIO)} partite create.')
        print('\nAvvia l\'app con:  python run.py')


if __name__ == '__main__':
    no_wipe = '--no-wipe' in sys.argv
    seed(wipe=not no_wipe)
