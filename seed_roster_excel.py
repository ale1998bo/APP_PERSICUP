# -*- coding: utf-8 -*-
"""
Importa le rose dal file Excel delle iscrizioni e aggiorna Firestore.
Salta la riga "juve" (test).

Uso:
    python seed_roster_excel.py
"""

import unicodedata
from app import create_app
from app.extensions import db

app = create_app('dev')

# ── Dati estratti dall'Excel ────────────────────────────────────────────────
# { nome_squadra_excel: [lista_giocatori_nome_cognome] }
ROSTER_EXCEL = {
    'Bartolini srl': [
        'Daniele Imbimbo', 'Thomas Espedito', 'Antonio Tucci', 'Nicolò Cremonini',
        'Mattia Restani', 'Nicolò Greco', 'Pietro Felicani', 'Angelo Capuano',
        'Federico Berni', 'Luca Gogliormella', 'Mattia Allegretti', 'Nicolò Cinelli',
        'Rigel Nichola',
    ],
    'M&M PARRUCCHIERI - ORIONE': [
        'Lorenzo Guarino', 'Lorenzo Vivarelli', 'Daniel Pierre Mayele', 'Gianluca Busi',
        'Simone Guarino', 'Davide Melandri', 'Filippo Pessarelli', 'Enrico Bertazzini',
        'Simone Ganzaroli', 'Cristian Zanetti', 'Mattia Cocchiarella', 'Enrico Mura',
    ],
    'Il Barone Rosso': [
        'Nicholas Sabbatini', 'Diego Cotti', 'Davide Cevolani', 'Nizar Okba',
        'Giovanni Stefani', 'Zied Ben Messallem', 'Nicoló Puopolo', 'Paolo Zaniboni',
        'Enrico Cheli', 'Matteo Cantarello', 'Nicola Timperio', 'Sallim Golinelli',
        'Cristian Cotti',
    ],
    'DECIMACAR': [
        'Alessandro Gamberini', 'Matteo Gamberini', 'Giuseppe Piccolo', 'Jacopo Panariello',
        'Adam Saleh Selim', 'Alessandro Vacchi', 'Davide Tesini', 'Lorenzo Bernaroli',
        "Jacopo Dall'olio", 'Edoardo Musat', 'Nicolò Vicenzi',
    ],
    'Alpha Wolf': [
        'Domenico Malino', 'Filippo Mogavero', 'Mounir Ibnou', 'Antonio Beneduce',
        'Samuele Serpetti', 'Tanimu Musah Azindow', 'Momodu Jerry', 'Omar El Kihel',
        'Franklin Yayra Tecku', 'Kasmi Mohammed', 'Szymon Choliwinski',
        'Christian Mogavero', 'Ibrahim Samsam', 'Mohamed Ali Haddaji', 'Mehdi El Boukhari',
    ],
    'La Rotonda Sul Pane': [
        'Simone Margotta', 'Matteo Morisi', 'Lorenzo Iattoni', 'Mehdi Elatachi',
        'Leonardo Boriani', 'Lorenzo Magli', 'Enea Cehu', 'Diego Cantelli',
        'Ismail Bahi', 'Djaber Nait', 'Giacomo Sandrolini', 'Enrico Tarozzi',
        'Leonard Assouan', 'Mohamed Erihoui', 'Luigi Ciarlantini',
    ],
    'Pizzeria da Palma': [
        'Andrea Pagliarella', 'Martino Santopadre', 'Giovanni Santopadre', 'Alejandro Ravaglia',
        'Fabrizio Zamboni', 'Marco Felicani', 'Alessandro Quaquarelli', 'Vittorio Gaiani',
        'Mattia Baiesi', 'Davide Cirelli', 'Justin Matias Imbrea', 'Luca Carbone',
    ],
    'Ficaroless': [
        'Matteo Tassinari', 'Mattia Pigaiani', 'Nicolò Verzieri', 'Matteo Mazzali',
        'Riccardo Fallavena', 'Enrico Lenzi', 'Andrea Rimondi', 'Alessandro Golinelli',
        'Alessandro Coraini', 'Elia Pedini', 'Lorenzo Bergamaschi', 'Riccardo Veronese',
        'Emanuele Manservisi', 'Nicola Martino', 'Michele Cedrelli',
    ],
    'CISANOVA': [
        'Tommaso Guerzoni', 'Nicolo Chinappi', 'Federico Nicoli', 'Tommaso Bongiovanni',
        'Filippo Bongiovanni', 'Elia Mingozzi', 'Samuel Malaguti', 'Jacopo Barbieri',
        'Nicolo Scagliarini', 'Filippo Forni', 'Giulio Meletti', 'Tommaso Cioni',
        'Matteo Quaquarelli', 'Mirco Milzani', 'Thomas Rimondi',
    ],
    'REAL TEMPO AMS': [
        'Olgert Xoxha', 'Hicham Agharda', 'Allen Kalaja', 'Cristian Castro Vazquez',
        'Damiano Pistone', 'Ousmane Seck', 'Matteo Storci', 'Gianluca Gattor',
        'Mohamed Bahi', 'Matteo Macchiaroli', 'Edoardo Stefani', 'Rosario Diletto',
        'Elnatan Ghebreselassie', 'Lorenzo Kolaveri', 'Julie Vanel Fotso',
    ],
    'Castellì e Tortellì': [
        'Federico Marsigli', 'Riccardo Ragazzi', 'Francesco Cumani', 'Hicham Baattout',
        'Cristian Castellini', 'Gabriele Gambino', 'Mattia Bisonti', 'Giacomo Berselli',
        'Antonio Caccavale', 'Mert Tasbasi', 'Mattia Scurani', 'Giovanni Nicoli',
        'Pierfilippo Gandolfi', 'Matteo Ferri', 'Sebastiano Gomez',
    ],
    'Old Money': [
        'Giovanni Scarale', 'Matteo Burroni', 'Lorenzo Sandri', 'Andrea Ruisi',
        'Simone Simonetti', 'Lorenzo Lusetti', 'Francesco Biagini', 'Alessandro Fiducia',
        'Giovanni Montanari', 'Massimiliano Ravaglia',
    ],
    'Loco Cafè': [
        'Alessandro Tuminelli', 'Gianluca Cotti', 'Samuele Barioni', 'Mattia Fiore',
        'Davide Sagliano', 'Andrea Cantelli', 'Mattia Zanfini', 'Yassin Abdallah',
        'Luca Bacci', 'David Forni', 'Samuele Parmeggiani', 'Fabio Girotti',
    ],
    'STABACCO': [
        'Marco Trombetta', 'Matteo Iandolo', 'Federico Roncarati', 'Federico Bonacorsi',
        'Alex Mazzoni', 'Diego Altafini', 'Luca Bettini', 'Alan Grazia',
        'Michele Trombetta', 'Manuele Cristiani', 'Simone Cassoli', 'Antonio Golisciano',
        'Gianmaria Boccalupo', 'Federico Paolucci', 'Matteo Tenisi',
    ],
    'Pizzeria Mirò Calderara': [
        'Andrea Ferrari', 'Nickolas Cinti', 'Francesco Colliva', 'Cataldo Graziano',
        'Matteo Boldrini', 'Simone Battilani', 'Nicolas Rondinelli', 'Riccardo Rotatori',
        'Ettore Fantasia', 'Samuele Vitarelli', 'Amhed Blaini', 'Giammarco Bertinelli',
        'Simone Severi', 'Matteo Urru', 'Lorenzo Fabbri',
    ],
}


def normalize(s):
    """Lowercase + rimuovi accenti per confronto fuzzy."""
    return ''.join(
        c for c in unicodedata.normalize('NFD', s.lower())
        if unicodedata.category(c) != 'Mn'
    )


def build_player(full_name):
    parts = full_name.strip().split(' ', 1)
    return {
        'nome': parts[0],
        'cognome': parts[1] if len(parts) > 1 else '',
        'scadenza_visita_medica': None,
        'file_visita': None,
    }


with app.app_context():
    teams_fs = db.collection('teams').stream()
    teams_map = {}
    for doc in teams_fs:
        d = doc.to_dict()
        teams_map[normalize(d.get('name', ''))] = {'id': doc.id, 'name': d.get('name')}

    updated = []
    not_found = []

    for excel_name, players in ROSTER_EXCEL.items():
        key = normalize(excel_name)
        team = teams_map.get(key)

        # Fallback: cerca per sottostringa
        if not team:
            for k, v in teams_map.items():
                if key in k or k in key:
                    team = v
                    break

        if not team:
            not_found.append(excel_name)
            continue

        roster = [build_player(p) for p in players]
        db.collection('teams').document(team['id']).update({'roster': roster})
        updated.append(f"  OK {team['name']} ({len(roster)} giocatori)")

    print("\n=== AGGIORNATE ===")
    for r in updated:
        print(r)

    if not_found:
        print("\n=== NON TROVATE (verifica nome) ===")
        for n in not_found:
            print(f"  NO {n}")

    print(f"\nDone: {len(updated)} squadre aggiornate, {len(not_found)} non trovate.")
