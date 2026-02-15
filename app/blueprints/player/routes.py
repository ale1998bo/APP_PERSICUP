import os
import uuid
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app.extensions import db
from app.models import RosterPlayer
from app.blueprints.auth.routes import role_required

player_bp = Blueprint('player', __name__, url_prefix='/player')

ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'gif', 'webp'}


def _allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# ── Roster Management (Captain Only) ───────────────────────────────────────
@player_bp.route('/roster', methods=['GET', 'POST'])
@role_required('capitano')
def roster():
    """Captain's roster management — add/view players with medical certificates."""
    team = current_user.team
    if not team:
        flash('Il tuo account non e associato a nessuna squadra.', 'danger')
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
                scadenza = datetime.strptime(scadenza_str, '%Y-%m-%d').date()
            except ValueError:
                flash('Data non valida.', 'danger')
                return redirect(url_for('player.roster'))

        # Handle file upload
        filename_saved = None
        file = request.files.get('visita_medica')
        if file and file.filename and _allowed_file(file.filename):
            ext = file.filename.rsplit('.', 1)[1].lower()
            unique_name = f"{uuid.uuid4().hex}.{ext}"
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_name)
            file.save(filepath)
            filename_saved = unique_name

        player = RosterPlayer(
            team_id=team.id,
            nome=nome,
            cognome=cognome,
            scadenza_visita_medica=scadenza,
            file_visita_medica=filename_saved,
        )
        db.session.add(player)
        db.session.commit()
        flash(f'Giocatore {nome} {cognome} aggiunto alla rosa.', 'success')
        return redirect(url_for('player.roster'))

    # GET
    roster_players = RosterPlayer.query.filter_by(team_id=team.id).order_by(RosterPlayer.cognome).all()
    return render_template('player/roster.html', team=team, roster_players=roster_players)


# ── Delete Roster Player ───────────────────────────────────────────────────
@player_bp.route('/roster/delete/<int:player_id>', methods=['POST'])
@role_required('capitano')
def delete_roster_player(player_id):
    """Remove a player from the roster."""
    team = current_user.team
    player = db.session.get(RosterPlayer, player_id)

    if not player or player.team_id != team.id:
        flash('Giocatore non trovato.', 'danger')
        return redirect(url_for('player.roster'))

    # Delete uploaded file if exists
    if player.file_visita_medica:
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], player.file_visita_medica)
        if os.path.exists(filepath):
            os.remove(filepath)

    name = f"{player.nome} {player.cognome}"
    db.session.delete(player)
    db.session.commit()
    flash(f'Giocatore {name} rimosso dalla rosa.', 'success')
    return redirect(url_for('player.roster'))
