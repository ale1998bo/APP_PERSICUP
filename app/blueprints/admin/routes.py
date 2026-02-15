from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required
from app.extensions import db
from app.models import User, Team, Match, Goal, RosterPlayer
from app.blueprints.auth.routes import role_required

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


# ── User Management ────────────────────────────────────────────────────────
@admin_bp.route('/users', methods=['GET', 'POST'])
@role_required('admin')
def user_management():
    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'create':
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '')
            role = request.form.get('role', 'giocatore')
            team_id = request.form.get('team_id', type=int)

            if not username or not password:
                flash('Username e password sono obbligatori.', 'danger')
            elif User.query.filter_by(username=username).first():
                flash(f'L\'utente "{username}" esiste gia.', 'danger')
            else:
                user = User(username=username, role=role)
                if role in ('giocatore', 'capitano') and team_id:
                    user.team_id = team_id
                user.set_password(password)
                db.session.add(user)
                db.session.commit()
                flash(f'Utente "{username}" creato con ruolo {role}.', 'success')

        elif action == 'delete':
            user_id = request.form.get('user_id', type=int)
            user = db.session.get(User, user_id)
            if user:
                db.session.delete(user)
                db.session.commit()
                flash(f'Utente "{user.username}" eliminato.', 'success')

        return redirect(url_for('admin.user_management'))

    users = User.query.order_by(User.role, User.username).all()
    teams = Team.query.order_by(Team.group, Team.name).all()
    return render_template('admin/users.html', users=users, teams=teams)


# ── Dashboard ───────────────────────────────────────────────────────────────
@admin_bp.route('/')
@role_required('admin', 'organizzatore')
def dashboard():
    total_teams = Team.query.count()
    total_matches = Match.query.count()
    played_matches = Match.query.filter_by(played=True).count()
    group_matches = Match.query.filter_by(phase='group').count()
    playoff_matches = Match.query.filter(Match.phase != 'group').count()

    return render_template(
        'admin/dashboard.html',
        total_teams=total_teams,
        total_matches=total_matches,
        played_matches=played_matches,
        group_matches=group_matches,
        playoff_matches=playoff_matches,
    )


# ── Match Manager (List — click to detail) ─────────────────────────────────
@admin_bp.route('/matches')
@role_required('admin', 'organizzatore')
def match_manager():
    group_matches = Match.query.filter_by(phase='group').order_by(Match.group, Match.id).all()
    playoff_matches = Match.query.filter(Match.phase != 'group').order_by(Match.id).all()

    return render_template(
        'admin/match_manager.html',
        group_matches=group_matches,
        playoff_matches=playoff_matches,
    )


# ── Match Detail (add scorers, MVP) ────────────────────────────────────────
@admin_bp.route('/match/<int:match_id>', methods=['GET', 'POST'])
@role_required('admin', 'organizzatore')
def match_detail(match_id):
    match = db.session.get(Match, match_id)
    if not match:
        flash('Partita non trovata.', 'danger')
        return redirect(url_for('admin.match_manager'))

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'add_goal':
            player_name = request.form.get('player_name', '').strip()
            team_id = request.form.get('team_id', type=int)
            minute = request.form.get('minute', type=int)

            if not player_name or team_id not in (match.home_team_id, match.away_team_id):
                flash('Dati marcatore non validi.', 'danger')
            else:
                goal = Goal(
                    match_id=match.id,
                    team_id=team_id,
                    player_name=player_name,
                    minute=minute,
                )
                db.session.add(goal)
                db.session.flush()
                match.recalc_score()
                db.session.commit()
                flash(f'Gol di {player_name} registrato.', 'success')

        elif action == 'delete_goal':
            goal_id = request.form.get('goal_id', type=int)
            goal = db.session.get(Goal, goal_id)
            if goal and goal.match_id == match.id:
                db.session.delete(goal)
                db.session.flush()
                match.recalc_score()
                if match.goals.count() == 0 and not match.man_of_match:
                    match.played = False
                    match.home_score = 0
                    match.away_score = 0
                db.session.commit()
                flash('Gol rimosso.', 'success')

        elif action == 'set_mvp':
            mvp_name = request.form.get('man_of_match', '').strip()
            match.man_of_match = mvp_name if mvp_name else None
            if not match.played and mvp_name:
                match.played = True
            db.session.commit()
            flash('Miglior giocatore aggiornato.', 'success')

        elif action == 'mark_played':
            match.played = True
            db.session.commit()
            flash('Partita segnata come giocata (0-0).', 'success')

        return redirect(url_for('admin.match_detail', match_id=match.id))

    # GET
    home_goals = Goal.query.filter_by(match_id=match.id, team_id=match.home_team_id)\
                     .order_by(Goal.minute).all()
    away_goals = Goal.query.filter_by(match_id=match.id, team_id=match.away_team_id)\
                     .order_by(Goal.minute).all()

    # Roster players for dropdown selection
    home_roster = RosterPlayer.query.filter_by(team_id=match.home_team_id)\
                       .order_by(RosterPlayer.cognome).all()
    away_roster = RosterPlayer.query.filter_by(team_id=match.away_team_id)\
                       .order_by(RosterPlayer.cognome).all()

    return render_template(
        'admin/match_detail.html',
        match=match,
        home_goals=home_goals,
        away_goals=away_goals,
        home_roster=home_roster,
        away_roster=away_roster,
    )


# ── Admin Roster Management ─────────────────────────────────────────────────
@admin_bp.route('/roster', methods=['GET'])
@admin_bp.route('/roster/<int:team_id>', methods=['GET', 'POST'])
@role_required('admin')
def admin_roster(team_id=None):
    """Admin can manage rosters for ALL teams."""
    import os, uuid
    from werkzeug.utils import secure_filename
    from datetime import datetime as dt

    ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'gif', 'webp'}

    teams = Team.query.order_by(Team.group, Team.name).all()

    if team_id is None:
        return render_template('admin/roster.html', teams=teams, selected_team=None, roster_players=[])

    team = db.session.get(Team, team_id)
    if not team:
        flash('Squadra non trovata.', 'danger')
        return redirect(url_for('admin.admin_roster'))

    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        cognome = request.form.get('cognome', '').strip()
        scadenza_str = request.form.get('scadenza_visita_medica', '').strip()

        if not nome or not cognome:
            flash('Nome e cognome sono obbligatori.', 'danger')
            return redirect(url_for('admin.admin_roster', team_id=team_id))

        scadenza = None
        if scadenza_str:
            try:
                scadenza = dt.strptime(scadenza_str, '%Y-%m-%d').date()
            except ValueError:
                flash('Data non valida.', 'danger')
                return redirect(url_for('admin.admin_roster', team_id=team_id))

        filename_saved = None
        file = request.files.get('visita_medica')
        if file and file.filename:
            ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
            if ext in ALLOWED_EXTENSIONS:
                from flask import current_app
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
        flash(f'Giocatore {nome} {cognome} aggiunto alla rosa di {team.name}.', 'success')
        return redirect(url_for('admin.admin_roster', team_id=team_id))

    roster_players = RosterPlayer.query.filter_by(team_id=team_id).order_by(RosterPlayer.cognome).all()
    return render_template('admin/roster.html', teams=teams, selected_team=team, roster_players=roster_players)


@admin_bp.route('/roster/delete/<int:player_id>', methods=['POST'])
@role_required('admin')
def admin_roster_delete(player_id):
    """Admin deletes a player from any roster."""
    import os
    player = db.session.get(RosterPlayer, player_id)
    if not player:
        flash('Giocatore non trovato.', 'danger')
        return redirect(url_for('admin.admin_roster'))

    team_id = player.team_id
    if player.file_visita_medica:
        from flask import current_app
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], player.file_visita_medica)
        if os.path.exists(filepath):
            os.remove(filepath)

    name = f"{player.nome} {player.cognome}"
    db.session.delete(player)
    db.session.commit()
    flash(f'Giocatore {name} rimosso dalla rosa.', 'success')
    return redirect(url_for('admin.admin_roster', team_id=team_id))


# ── Generate Playoffs ───────────────────────────────────────────────────────
@admin_bp.route('/generate-playoffs', methods=['POST'])
@role_required('admin')
def generate_playoffs():
    """
    Reads final group standings and creates Quarter-Final matches:
      Q1: 1st A vs 2nd B
      Q2: 1st C vs 2nd D
      Q3: 1st B vs 2nd A
      Q4: 1st D vs 2nd C
    """
    from app.blueprints.main.routes import get_standings

    # Check: all group matches must be played
    unplayed = Match.query.filter_by(phase='group', played=False).count()
    if unplayed > 0:
        flash(f'Ci sono ancora {unplayed} partite dei gironi da giocare.', 'warning')
        return redirect(url_for('admin.dashboard'))

    # Check: playoffs not already generated
    existing = Match.query.filter_by(phase='quarter').count()
    if existing > 0:
        flash('I quarti di finale sono già stati generati.', 'warning')
        return redirect(url_for('admin.dashboard'))

    # Get standings for each group
    standings = {}
    for g in ['A', 'B', 'C', 'D']:
        standings[g] = get_standings(g)

    # Quarter-final pairings
    pairings = [
        (standings['A'][0]['team'], standings['B'][1]['team']),  # Q1
        (standings['C'][0]['team'], standings['D'][1]['team']),  # Q2
        (standings['B'][0]['team'], standings['A'][1]['team']),  # Q3
        (standings['D'][0]['team'], standings['C'][1]['team']),  # Q4
    ]

    for home, away in pairings:
        match = Match(
            home_team_id=home.id,
            away_team_id=away.id,
            phase='quarter',
        )
        db.session.add(match)

    db.session.commit()
    flash('Quarti di finale generati con successo!', 'success')
    return redirect(url_for('admin.match_manager'))

