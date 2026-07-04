import uuid
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from app.extensions import db
from app.models import Team
from app.blueprints.auth.routes import role_required
from app.storage import upload_file, delete_file

player_bp = Blueprint('player', __name__, url_prefix='/player')

ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'gif', 'webp'}

def _allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# ── Roster Management (Captain Only) ───────────────────────────────────────
@player_bp.route('/roster', methods=['GET', 'POST'])
@role_required('capitano')
def roster():
    """Captain's roster management — add/view players with medical certificates."""
    team_id = current_user.team_id
    if not team_id:
        flash('Il tuo account non e associato a nessuna squadra.', 'danger')
        return redirect(url_for('main.index'))
        
    team = Team.get_by_id(team_id)
    if not team:
        flash('Squadra associata inesistente.', 'danger')
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        cognome = request.form.get('cognome', '').strip()
        scadenza_str = request.form.get('scadenza_visita_medica', '').strip()

        if not nome or not cognome:
            flash('Nome e cognome sono obbligatori.', 'danger')
            return redirect(url_for('player.roster'))

        # Parse date
        scadenza = None
        if scadenza_str:
            try:
                scadenza = datetime.strptime(scadenza_str, '%Y-%m-%d').date().isoformat()
            except ValueError:
                flash('Data non valida.', 'danger')
                return redirect(url_for('player.roster'))

        # Handle file upload
        filename_saved = None
        file = request.files.get('visita_medica')
        if file and file.filename and _allowed_file(file.filename):
            ext = file.filename.rsplit('.', 1)[1].lower()
            unique_name = f"{uuid.uuid4().hex}.{ext}"
            upload_file(file, unique_name)
            filename_saved = unique_name

        player_data = {
            'nome': nome,
            'cognome': cognome,
            'scadenza_visita_medica': scadenza,
            'file_visita_medica': filename_saved,
        }
        Team.add_player_to_roster(team_id, player_data)
        flash(f'Giocatore {nome} {cognome} aggiunto alla rosa.', 'success')
        return redirect(url_for('player.roster'))

    # GET
    roster_players = team.get('roster', [])
    # Re-sort for display (equivalent to order_by(cognome))
    roster_players.sort(key=lambda p: p.get('cognome', '').lower())
    from datetime import datetime as dt
    today = dt.today().date().isoformat()
    return render_template('player/roster.html', team=team, roster_players=roster_players, today=today)


# ── Delete Roster Player ───────────────────────────────────────────────────
@player_bp.route('/roster/delete/<cognome>', methods=['POST'])
@role_required('capitano')
def delete_roster_player(cognome):
    """Remove a player from the roster array."""
    team_id = current_user.team_id
    if not team_id:
        return redirect(url_for('player.roster'))

    team = Team.get_by_id(team_id)
    if not team:
        flash('Squadra non trovata.', 'danger')
        return redirect(url_for('player.roster'))

    new_roster = []
    found = False
    
    for p in team.get('roster', []):
        if p.get('cognome') == cognome and not found:
            found = True
            if p.get('file_visita_medica'):
                delete_file(p['file_visita_medica'])
            continue
        new_roster.append(p)

    if found:
        db.collection(Team.collection_name).document(team_id).update({'roster': new_roster})
        flash(f'Giocatore rimosso dalla rosa.', 'success')
    else:
        flash(f'Giocatore non trovato nella rosa.', 'danger')
        
    return redirect(url_for('player.roster'))
