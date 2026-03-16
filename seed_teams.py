import os
from app import create_app
from app.extensions import db
from app.models import Team, Match
from google.cloud import firestore

app = create_app()

def reset_and_seed_teams():
    with app.app_context():
        print("Connesso a Firestore...")
        
        # 1. Elimina le vecchie partite per evitare riferimenti orfani a squadre inesistenti
        print("Scansione partite da rimuovere...")
        matches_ref = db.collection(Match.collection_name).stream()
        matches_deleted = 0
        for match in matches_ref:
            match.reference.delete()
            matches_deleted += 1
        print(f"Eliminate {matches_deleted} partite precedenti.")

        # 2. Elimina i vecchi team
        print("Scansione squadre da rimuovere...")
        teams_ref = db.collection(Team.collection_name).stream()
        teams_deleted = 0
        for team in teams_ref:
            team.reference.delete()
            teams_deleted += 1
        print(f"Eliminate {teams_deleted} squadre precedenti.")

        # 3. Creazione di 16 nuove squadre (4 per girone A, B, C, D)
        print("\nCreazione di 16 nuove squadre...")
        squadre_nomi = [
            "Real Madrid", "Barcellona", "Bayern Monaco", "Manchester City", # Girone A
            "Liverpool", "Paris Saint-Germain", "Juventus", "Inter",         # Girone B
            "Milan", "Arsenal", "Chelsea", "Borussia Dortmund",              # Girone C
            "Atletico Madrid", "Napoli", "Benfica", "Porto"                  # Girone D
        ]
        
        gironi = ['A', 'A', 'A', 'A', 'B', 'B', 'B', 'B', 'C', 'C', 'C', 'C', 'D', 'D', 'D', 'D']
        
        squadre_create = 0
        for nome, girone in zip(squadre_nomi, gironi):
            Team.create(name=nome, group=girone)
            squadre_create += 1
            print(f" - Creata squadra: {nome} (Girone {girone})")
            
        print(f"\nOperazione completata con successo! {squadre_create} squadre inserite nel database Firestore.")

if __name__ == "__main__":
    reset_and_seed_teams()
