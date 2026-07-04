# -*- coding: utf-8 -*-
"""
Seed completo per testare l'app:
  - Pulisce le collezioni 'teams' e 'matches' su Firestore
  - Crea 16 squadre (4 gironi A/B/C/D), ciascuna con 15 giocatori in rosa
  - Crea le 6 partite di girone all'italiana per ogni girone (24 partite totali)
  - Programma le partite per OGGI in 6 fasce orarie (16:00, 17:00, 18:00, 19:00, 20:00, 21:00),
    4 partite contemporanee per fascia (una per girone)
  - Simula tutti i risultati con goal realistici e marcatori presi dalla rosa

Uso:
    python seed_full.py
"""

import random
from datetime import date, datetime, timedelta

DURATA_PARTITA_MIN = 40

from app import create_app
from app.extensions import db
from app.models import Team, Match
from google.cloud import firestore


# ── Dati statici ────────────────────────────────────────────────────────────
SQUADRE_PER_GIRONE = {
    'A': ['Real Madrid', 'Barcellona', 'Bayern Monaco', 'Manchester City'],
    'B': ['Liverpool', 'Paris Saint-Germain', 'Juventus', 'Inter'],
    'C': ['Milan', 'Arsenal', 'Chelsea', 'Borussia Dortmund'],
    'D': ['Atletico Madrid', 'Napoli', 'Benfica', 'Porto'],
}

NOMI = [
    'Marco', 'Luca', 'Giuseppe', 'Andrea', 'Francesco', 'Alessandro', 'Matteo',
    'Davide', 'Stefano', 'Roberto', 'Lorenzo', 'Simone', 'Antonio', 'Federico',
    'Paolo', 'Riccardo', 'Daniele', 'Gabriele', 'Giovanni', 'Tommaso',
    'Emanuele', 'Nicola', 'Filippo', 'Edoardo', 'Michele', 'Cristian',
    'Salvatore', 'Vincenzo', 'Mattia', 'Leonardo', 'Samuele', 'Diego',
    'Pietro', 'Enrico', 'Fabio',
]

COGNOMI = [
    'Rossi', 'Russo', 'Ferrari', 'Esposito', 'Bianchi', 'Romano', 'Colombo',
    'Ricci', 'Marino', 'Greco', 'Bruno', 'Gallo', 'Conti', 'De Luca',
    'Mancini', 'Costa', 'Giordano', 'Rizzo', 'Lombardi', 'Moretti',
    'Barbieri', 'Fontana', 'Santoro', 'Mariani', 'Rinaldi', 'Caruso',
    'Ferrara', 'Galli', 'Martini', 'Leone', 'Longo', 'Gentile', 'Martinelli',
    'Vitale', 'Lombardo',
]


# ── Helper ──────────────────────────────────────────────────────────────────
def wipe_collection(collection_name):
    """Elimina tutti i documenti di una collezione."""
    deleted = 0
    for doc in db.collection(collection_name).stream():
        doc.reference.delete()
        deleted += 1
    return deleted


def make_roster(rng, n=15):
    """Genera 15 giocatori unici con visita medica valida (6 mesi nel futuro)."""
    visita = (date.today() + timedelta(days=180)).isoformat()
    used = set()
    roster = []
    while len(roster) < n:
        nome = rng.choice(NOMI)
        cognome = rng.choice(COGNOMI)
        key = (nome, cognome)
        if key in used:
            continue
        used.add(key)
        roster.append({
            'nome': nome,
            'cognome': cognome,
            'scadenza_visita_medica': visita,
            'file_visita_medica': None,
        })
    return roster


def round_robin_pairs(teams):
    """Coppie round-robin per 4 squadre — stesso ordine usato dall'admin."""
    return [
        (teams[0], teams[1]), (teams[2], teams[3]),
        (teams[0], teams[2]), (teams[1], teams[3]),
        (teams[0], teams[3]), (teams[1], teams[2]),
    ]


def simulate_goals(home_team, away_team, rng):
    """Genera score realistico (0-4) e marcatori scelti dalla rosa."""
    home_score = rng.choices([0, 1, 2, 3, 4], weights=[15, 30, 30, 15, 10])[0]
    away_score = rng.choices([0, 1, 2, 3, 4], weights=[20, 30, 28, 15, 7])[0]

    goals = []
    minutes_used = set()

    def add(team, score):
        roster = team.get('roster', [])
        for _ in range(score):
            # minuto unico per partita per non avere collisioni nel template
            while True:
                minute = rng.randint(1, 40)
                if minute not in minutes_used:
                    minutes_used.add(minute)
                    break
            if roster:
                p = rng.choice(roster)
                name = f"{p['nome']} {p['cognome']}"
            else:
                name = 'Giocatore'
            goals.append({
                'team_id': team['id'],
                'player_name': name,
                'minute': minute,
            })

    add(home_team, home_score)
    add(away_team, away_score)
    goals.sort(key=lambda g: g['minute'])
    return home_score, away_score, goals


# ── Main ────────────────────────────────────────────────────────────────────
def seed():
    app = create_app()
    rng = random.Random(42)  # seed fisso → riproducibile

    with app.app_context():
        print('Connesso a Firestore.')

        # 1. Pulizia
        n_m = wipe_collection(Match.collection_name)
        n_t = wipe_collection(Team.collection_name)
        print(f'[OK] Pulite {n_t} squadre e {n_m} partite preesistenti.')

        # 2. Crea squadre con roster da 15
        print('\nCreazione squadre + rose (15 giocatori ciascuna)...')
        teams_by_group = {g: [] for g in SQUADRE_PER_GIRONE}
        for girone, nomi in SQUADRE_PER_GIRONE.items():
            for nome in nomi:
                roster = make_roster(rng)
                team_data = {
                    'name': nome,
                    'group': girone,
                    'logo_url': '',
                    'roster': roster,
                }
                _, ref = db.collection(Team.collection_name).add(team_data)
                team_data['id'] = ref.id
                teams_by_group[girone].append(team_data)
                print(f"  - {nome} (Girone {girone}) - {len(roster)} giocatori")

        # 3. Crea le 24 partite di girone distribuite su 4 giornate consecutive
        # 6 partite/giorno = 2 contemporanee x 3 fasce (16:00, 17:00, 18:00)
        print('\nCreazione partite di girone con calendario (4 giornate)...')
        oggi = date.today()
        date_giornate = [(oggi + timedelta(days=g)).isoformat() for g in range(4)]
        orari = ['16:00', '17:00', '18:00']

        # Per ogni girone, 6 partite organizzate in 3 turni round-robin da 2 match
        # ogni turno coinvolge tutte e 4 le squadre senza ripetizioni.
        pairs_per_girone = {g: round_robin_pairs(t) for g, t in teams_by_group.items()}

        def turno(girone_key, turno_idx):
            start = turno_idx * 2
            return pairs_per_girone[girone_key][start:start + 2]

        # Calendario bilanciato: ogni giornata ospita 3 turni (= 6 match) di 3 gironi diversi.
        # Cosi` ogni squadra gioca al massimo 1 volta al giorno e ogni girone gioca in 3
        # giornate su 4. Tutti i turni (3 x 4 = 12) finiscono nel calendario.
        giornate_turni = [
            [('A', 0), ('B', 0), ('C', 0)],  # G1
            [('A', 1), ('B', 1), ('D', 0)],  # G2
            [('A', 2), ('C', 1), ('D', 1)],  # G3
            [('B', 2), ('C', 2), ('D', 2)],  # G4
        ]

        match_records = []
        for giornata_idx, turni in enumerate(giornate_turni):
            # turni = [(gironeX, turnoX), (gironeY, turnoY), (gironeZ, turnoZ)]
            (gX, tX), (gY, tY), (gZ, tZ) = turni
            mX = turno(gX, tX)  # 2 match girone X
            mY = turno(gY, tY)
            mZ = turno(gZ, tZ)

            # 3 fasce orarie (16/17/18), 2 match per fascia di gironi distinti:
            #   16:00 -> X[0] + Y[0]
            #   17:00 -> X[1] + Z[0]
            #   18:00 -> Y[1] + Z[1]
            fasce_match = [
                [(gX, *mX[0]), (gY, *mY[0])],
                [(gX, *mX[1]), (gZ, *mZ[0])],
                [(gY, *mY[1]), (gZ, *mZ[1])],
            ]

            for fascia_idx, partite_fascia in enumerate(fasce_match):
                match_date = date_giornate[giornata_idx]
                match_time = orari[fascia_idx]
                for girone, home, away in partite_fascia:
                    match_data = {
                        'home_team_id': home['id'],
                        'away_team_id': away['id'],
                        'home_score': 0,
                        'away_score': 0,
                        'phase': 'group',
                        'group': girone,
                        'played': False,
                        'match_date': match_date,
                        'match_time': match_time,
                        'man_of_match': None,
                        'goals': [],
                    }
                    _, ref = db.collection(Match.collection_name).add(match_data)
                    match_records.append({
                        'id': ref.id,
                        'home': home,
                        'away': away,
                        'girone': girone,
                        'giornata': giornata_idx + 1,
                        'date': match_date,
                        'time': match_time,
                    })
                    print(f"  - G{giornata_idx + 1} [{girone}] {home['name']} vs {away['name']} -> {match_date} {match_time}")

        # 4. Simula solo le partite GIA' FINITE (start + 40 min <= adesso).
        #    Le LIVE e le future restano 0-0 / played=False.
        print('\nSimulazione risultati (solo partite gia` finite)...')
        now = datetime.now()
        n_played, n_live, n_future = 0, 0, 0

        for m in match_records:
            start = datetime.fromisoformat(f"{m['date']}T{m['time']}")
            end = start + timedelta(minutes=DURATA_PARTITA_MIN)

            if end <= now:
                # Partita finita -> simula
                home_score, away_score, goals = simulate_goals(m['home'], m['away'], rng)

                scorer_counts = {}
                for g in goals:
                    scorer_counts[g['player_name']] = scorer_counts.get(g['player_name'], 0) + 1
                if scorer_counts:
                    mvp = max(scorer_counts.items(), key=lambda kv: kv[1])[0]
                else:
                    winner = m['home'] if rng.random() < 0.5 else m['away']
                    p = rng.choice(winner['roster'])
                    mvp = f"{p['nome']} {p['cognome']}"

                db.collection(Match.collection_name).document(m['id']).update({
                    'home_score': home_score,
                    'away_score': away_score,
                    'goals': goals,
                    'played': True,
                    'man_of_match': mvp,
                })
                n_played += 1
                print(f"  - [GIOCATA G{m['giornata']} {m['time']}] {m['home']['name']} {home_score}-{away_score} {m['away']['name']}  MVP: {mvp}")
            elif start <= now < end:
                n_live += 1
                print(f"  - [LIVE     G{m['giornata']} {m['time']}] {m['home']['name']} vs {m['away']['name']}  (in corso)")
            else:
                n_future += 1

        # 5. Riepilogo
        tot_squadre = sum(len(v) for v in teams_by_group.values())
        tot_giocatori = tot_squadre * 15
        print('\n--------------------------------------------')
        print(f'[OK] {tot_squadre} squadre create ({tot_giocatori} giocatori in rosa)')
        print(f'[OK] {len(match_records)} partite create su {len(date_giornate)} giornate ({", ".join(date_giornate)})')
        print(f'[OK] Fasce orarie giornaliere: {", ".join(orari)}  (durata stimata partita: {DURATA_PARTITA_MIN} min)')
        print(f'[OK] Stato attuale: {n_played} giocate, {n_live} LIVE adesso, {n_future} da giocare')
        print('Avvia ora l\'app:  python run.py')


if __name__ == '__main__':
    seed()
