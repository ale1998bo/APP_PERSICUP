import os
import random
from app import create_app
from app.extensions import db
from app.models import Match

app = create_app()

def fill_matches():
    with app.app_context():
        # Get all matches
        matches = Match.get_all()
        # Find all unplayed group matches (phase == 'group')
        group_matches = [m for m in matches if m.get('phase') == 'group' and not m.get('played')]
        
        print(f"Found {len(group_matches)} unplayed group matches.")
        
        for m in group_matches:
            match_id = m['id']
            home_team_id = m['home_team_id']
            away_team_id = m['away_team_id']
            
            # Genera risultati casuali
            home_score = random.randint(0, 5)
            away_score = random.randint(0, 5)
            
            # Genera la lista dei goal
            goals = []
            for _ in range(home_score):
                goals.append({
                    'team_id': home_team_id,
                    'player_name': 'Player Home',
                    'minute': random.randint(1, 40)
                })
                
            for _ in range(away_score):
                goals.append({
                    'team_id': away_team_id,
                    'player_name': 'Player Away',
                    'minute': random.randint(1, 40)
                })
            
            # Aggiorna il documento su firestore
            doc_ref = db.collection(Match.collection_name).document(match_id)
            doc_ref.update({
                'home_score': home_score,
                'away_score': away_score,
                'played': True,
                'goals': goals
            })
            print(f"Match {match_id} updated: {home_score} - {away_score}")

if __name__ == '__main__':
    fill_matches()
    print("Tutte le partite dei gironi sono state simulate!")
