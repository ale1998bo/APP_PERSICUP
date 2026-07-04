from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required
from app.extensions import db
from app.models import User, Team, Match
from app.blueprints.auth.routes import role_required
from app.storage import upload_file, delete_file

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
            role = request.form.get('role', 'capitano')
            team_id = request.form.get('team_id')

            if not username or not password:
                flash('Username e password sono obbligatori.', 'danger')
            else:
                try:
                    User.create(username, password, role, team_id)
                    flash(f'Utente "{username}" creato con ruolo {role}.', 'success')
                except ValueError as e:
                    flash(str(e), 'danger')

        elif action == 'delete':
            uid = request.form.get('user_id')
            db.collection(User.collection_name).document(uid).delete()
            flash('Utente eliminato.', 'success')

        return redirect(url_for('admin.user_management'))

    users = []
    for doc in db.collection(User.collection_name).stream():
        d = doc.to_dict()
        d['id'] = doc.id
        users.append(d)
        
    teams = Team.get_all()
    # Sort
    users.sort(key=lambda x: (x.get('role') or '', x.get('username') or ''))
    teams.sort(key=lambda x: (x.get('group') or '', x.get('name') or ''))
    
    return render_template('admin/users.html', users=users, teams=teams)


# ── Dashboard ───────────────────────────────────────────────────────────────
@admin_bp.route('/')
@role_required('admin', 'organizzatore')
def dashboard():
    teams = Team.get_all()
    matches = Match.get_all()
    
    total_teams = len(teams)
    total_matches = len(matches)
    played_matches = len([m for m in matches if m.get('played')])
    group_matches = len([m for m in matches if m.get('phase') == 'group'])
    playoff_matches = len([m for m in matches if m.get('phase') != 'group'])

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
    matches = Match.get_all()
    teams = Team.get_all()
    
    group_matches = sorted([m for m in matches if m.get('phase') == 'group'], key=lambda x: (x.get('group') or '', x.get('id')))
    playoff_matches = sorted([m for m in matches if m.get('phase') != 'group'], key=lambda x: x.get('match_date') or x['id'])
    
    # helper for template mapping
    def attach_teams(m_list):
        for m in m_list:
            m['home_team'] = Team.get_by_id(m['home_team_id']) or {"name": "Sconosciuto"}
            m['away_team'] = Team.get_by_id(m['away_team_id']) or {"name": "Sconosciuto"}
        return m_list
        
    # Ordinamento squadre alfabeticamente
    teams.sort(key=lambda x: x.get('name', ''))

    # Lista unificata per filtri
    all_matches = attach_teams(group_matches) + attach_teams(playoff_matches)
    all_matches.sort(key=lambda x: (x.get('match_date') or '9999', x.get('match_time') or '99:99', x.get('group') or '', x['id']))

    # Gironi e date disponibili per i filtri
    available_groups = sorted(set(m['group'] for m in group_matches if m.get('group')))
    available_phases = sorted(set(m['phase'] for m in playoff_matches if m.get('phase')))
    available_dates = sorted(set(m['match_date'] for m in all_matches if m.get('match_date')))

    return render_template(
        'admin/match_manager.html',
        teams=teams,
        all_matches=all_matches,
        available_groups=available_groups,
        available_phases=available_phases,
        available_dates=available_dates,
    )


@admin_bp.route('/match-manager/generate-groups', methods=['POST'])
@role_required('admin', 'organizzatore')
def generate_group_matches():
    groups = ['A', 'B', 'C', 'D']
    created_count = 0
    for group in groups:
        # Check if matches already exist per questo girone per evitare over-posting
        existing = Match.get_by_group(group)
        if existing:
            continue
            
        teams = Team.get_by_group(group)
        if len(teams) != 4:
            continue # Needs exactly 4 teams per stilare un girone all'italiana standard
            
        # Round robin pairs for 4 teams: (0,1), (2,3), (0,2), (1,3), (0,3), (1,2)
        pairs = [
            (teams[0], teams[1]), (teams[2], teams[3]),
            (teams[0], teams[2]), (teams[1], teams[3]),
            (teams[0], teams[3]), (teams[1], teams[2])
        ]
        
        for t1, t2 in pairs:
            Match.create(home_team_id=t1['id'], away_team_id=t2['id'], group=group, phase='group')
            created_count += 1
            
    if created_count > 0:
        flash(f'Generazione automatica completata: {created_count} partite create.', 'success')
    else:
        flash('Nessuna partita generata. Controlla che i gironi abbiano 4 squadre o che non siano state già create.', 'warning')
        
    return redirect(url_for('admin.match_manager'))


# ── Match Detail (add scorers, MVP) ────────────────────────────────────────
@admin_bp.route('/match/<match_id>', methods=['GET', 'POST'])
@role_required('admin', 'organizzatore')
def match_detail(match_id):
    match = Match.get_by_id(match_id)
    if not match:
        flash('Partita non trovata.', 'danger')
        return redirect(url_for('admin.match_manager'))
        
    home_team = Team.get_by_id(match['home_team_id'])
    away_team = Team.get_by_id(match['away_team_id'])
    match['home_team'] = home_team
    match['away_team'] = away_team

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'add_goal':
            player_name = request.form.get('player_name', '').strip()
            team_id = request.form.get('team_id')
            minute_str = request.form.get('minute')
            minute = int(minute_str) if minute_str and minute_str.isdigit() else None
            is_own_goal = request.form.get('is_own_goal') == '1'

            if not player_name or team_id not in (match['home_team_id'], match['away_team_id']):
                flash('Dati marcatore non validi.', 'danger')
            else:
                # Autogol: il punto va alla squadra avversaria
                if is_own_goal:
                    scoring_team_id = match['away_team_id'] if team_id == match['home_team_id'] else match['home_team_id']
                else:
                    scoring_team_id = team_id
                Match.add_goal(match_id, scoring_team_id, player_name, minute, is_own_goal=is_own_goal)
                label = f'{player_name} (aut.)' if is_own_goal else player_name
                flash(f'Goal di {label} registrato.', 'success')

        elif action == 'delete_goal':
            # Firestore Non ha un vero e proprio Remove per elementi complessi in Array senza corrispondenza esatta,
            # lo facciamo via replacement dell'array intero.
            player_name_to_del = request.form.get('player_name')
            minute_to_del_str = request.form.get('minute')
            try:
                min_del = int(minute_to_del_str) if minute_to_del_str and minute_to_del_str != 'None' else None
            except:
                min_del = None
                
            goals = match.get('goals', [])
            new_goals = []
            deleted = False
            for g in goals:
                if not deleted and g['player_name'] == player_name_to_del and g['minute'] == min_del:
                    deleted = True # Delete solo la prima occorrenza
                    continue
                new_goals.append(g)
                
            db.collection(Match.collection_name).document(match_id).update({'goals': new_goals})
            Match.update_score_from_goals(match_id)
            flash('Goal rimosso.', 'success')

        elif action == 'set_mvp':
            mvp_name = request.form.get('man_of_match', '').strip()
            update_data = {'man_of_match': mvp_name if mvp_name else None}
            if not match.get('played') and mvp_name:
                update_data['played'] = True
            db.collection(Match.collection_name).document(match_id).update(update_data)
            flash('Miglior giocatore aggiornato.', 'success')

        elif action == 'mark_played':
            db.collection(Match.collection_name).document(match_id).update({'played': True, 'live': False})
            flash('Partita segnata come giocata.', 'success')

        elif action == 'mark_unplayed':
            db.collection(Match.collection_name).document(match_id).update({'played': False, 'live': False})
            flash('Partita riportata a "Da giocare".', 'success')

        elif action == 'mark_live':
            db.collection(Match.collection_name).document(match_id).update({'live': True})
            flash('Partita segnata come LIVE.', 'success')

        elif action == 'mark_not_live':
            db.collection(Match.collection_name).document(match_id).update({'live': False})
            flash('Stato LIVE rimosso.', 'success')

        elif action == 'set_datetime':
            match_date = request.form.get('match_date')
            match_time = request.form.get('match_time')
            Match.set_datetime(match_id, match_date, match_time)
            flash('Calendario aggiornato.', 'success')

        return redirect(url_for('admin.match_detail', match_id=match_id))

    # GET
    home_goals = [g for g in match.get('goals', []) if g['team_id'] == match['home_team_id']]
    away_goals = [g for g in match.get('goals', []) if g['team_id'] == match['away_team_id']]

    home_roster = home_team.get('roster', []) if home_team else []
    away_roster = away_team.get('roster', []) if away_team else []

    return render_template(
        'admin/match_detail.html',
        match=match,
        home_goals=home_goals,
        away_goals=away_goals,
        home_roster=home_roster,
        away_roster=away_roster,
    )


# ── Admin Roster Management ─────────────────────────────────────────────────
@admin_bp.route('/roster', methods=['GET', 'POST'])
@admin_bp.route('/roster/<team_id>', methods=['GET', 'POST'])
@role_required('admin', 'organizzatore')
def admin_roster(team_id=None):
    import os, uuid
    from datetime import datetime as dt

    ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'gif', 'webp'}

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'create_team':
            name = request.form.get('name', '').strip()
            if not name:
                flash('Il nome della squadra è obbligatorio.', 'danger')
            else:
                Team.create(name=name, group=None)
                flash(f'Squadra "{name}" creata con successo. (Girone da assegnare)', 'success')
            return redirect(url_for('admin.admin_roster', team_id=team_id))

        elif action == 'set_group':
            updated_team_id = request.form.get('team_id')
            new_group = request.form.get('group', '').strip()
            if updated_team_id and new_group:
                db.collection(Team.collection_name).document(updated_team_id).update({'group': new_group})
                flash('Girone assegnato con successo.', 'success')
            return redirect(url_for('admin.admin_roster', team_id=updated_team_id))

        elif action == 'delete_team':
            del_team_id = request.form.get('team_id')
            if del_team_id:
                db.collection(Team.collection_name).document(del_team_id).delete()
                flash('Squadra eliminata con successo.', 'success')
            return redirect(url_for('admin.admin_roster'))

        # -- Azione di default: Aggiunta gicatore (se team_id esiste) --
        if not team_id:
            flash('Squadra non trovata.', 'danger')
            return redirect(url_for('admin.admin_roster'))
            
        team = Team.get_by_id(team_id)
        if not team:
            flash('Squadra non trovata.', 'danger')
            return redirect(url_for('admin.admin_roster'))
            
        nome = request.form.get('nome', '').strip()
        cognome = request.form.get('cognome', '').strip()
        scadenza_str = request.form.get('scadenza_visita_medica', '').strip()

        if not nome or not cognome:
            flash('Nome e cognome sono obbligatori.', 'danger')
            return redirect(url_for('admin.admin_roster', team_id=team_id))

        scadenza = None
        if scadenza_str:
            try:
                scadenza = dt.strptime(scadenza_str, '%Y-%m-%d').date().isoformat()
            except ValueError:
                flash('Data non valida.', 'danger')
                return redirect(url_for('admin.admin_roster', team_id=team_id))

        filename_saved = None
        file = request.files.get('visita_medica')
        if file and file.filename:
            ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
            if ext in ALLOWED_EXTENSIONS:
                unique_name = f"{uuid.uuid4().hex}.{ext}"
                upload_file(file, unique_name)
                filename_saved = unique_name

        player_data = {
            'nome': nome,
            'cognome': cognome,
            'scadenza_visita_medica': scadenza,
            'file_visita_medica': filename_saved
        }
        Team.add_player_to_roster(team_id, player_data)
        flash(f'Giocatore {nome} {cognome} aggiunto alla rosa.', 'success')
        return redirect(url_for('admin.admin_roster', team_id=team_id))

    teams = Team.get_all()
    teams.sort(key=lambda x: (x.get('group') or '', x.get('name') or ''))
    
    if team_id is None:
        from datetime import datetime as dt
        today = dt.today().date().isoformat()
        return render_template('admin/roster.html', teams=teams, selected_team=None, roster_players=[], today=today)

    team = Team.get_by_id(team_id)
    if not team:
        return redirect(url_for('admin.admin_roster'))

    roster_players = team.get('roster', [])
    from datetime import datetime as dt
    today = dt.today().date().isoformat()
    return render_template('admin/roster.html', teams=teams, selected_team=team, roster_players=roster_players, today=today)


@admin_bp.route('/roster/delete/<team_id>/<cognome>', methods=['POST'])
@role_required('admin', 'organizzatore')
def admin_roster_delete(team_id, cognome):
    """Admin deletes a player from array (via re-assignment)."""
    team = Team.get_by_id(team_id)
    if not team:
        return redirect(url_for('admin.admin_roster'))
        
    new_roster = []
    for p in team.get('roster', []):
        if p.get('cognome') == cognome:
            if p.get('file_visita_medica'):
                delete_file(p['file_visita_medica'])
            continue
        new_roster.append(p)
        
    db.collection(Team.collection_name).document(team_id).update({'roster': new_roster})
    flash('Giocatore rimosso dalla rosa.', 'success')
    return redirect(url_for('admin.admin_roster', team_id=team_id))


# ── Manual Playoff Creation ─────────────────────────────────────────────────
@admin_bp.route('/match-manager/create-playoff', methods=['POST'])
@role_required('admin', 'organizzatore')
def create_playoff():
    home_team_id = request.form.get('home_team_id')
    away_team_id = request.form.get('away_team_id')
    phase = request.form.get('phase', '').strip()
    match_date = request.form.get('match_date', '').strip()
    match_time = request.form.get('match_time', '').strip()

    if not home_team_id or not away_team_id or not phase:
        flash('Compila tutti i campi obbligatori (Squadre e Fase).', 'danger')
        return redirect(url_for('admin.match_manager'))

    if home_team_id == away_team_id:
        flash('Una squadra non può giocare contro se stessa.', 'danger')
        return redirect(url_for('admin.match_manager'))

    # Crea la partita
    match_id = Match.create(home_team_id=home_team_id, away_team_id=away_team_id, group=None, phase=phase)
    
    # Se passati, salva data e ora
    if match_date or match_time:
        Match.set_datetime(match_id, match_date, match_time)

    flash('Partita di eliminazione diretta generata con successo.', 'success')
    return redirect(url_for('admin.match_manager'))


# ── Create Single Group Match ──────────────────────────────────────────────
@admin_bp.route('/match-manager/create-group', methods=['POST'])
@role_required('admin', 'organizzatore')
def create_group_match():
    home_team_id = request.form.get('home_team_id')
    away_team_id = request.form.get('away_team_id')
    group = request.form.get('group', '').strip()
    match_date = request.form.get('match_date', '').strip()
    match_time = request.form.get('match_time', '').strip()

    if not home_team_id or not away_team_id or not group:
        flash('Compila tutti i campi obbligatori (Squadre e Girone).', 'danger')
        return redirect(url_for('admin.match_manager'))

    if home_team_id == away_team_id:
        flash('Una squadra non può giocare contro se stessa.', 'danger')
        return redirect(url_for('admin.match_manager'))

    match_id = Match.create(home_team_id=home_team_id, away_team_id=away_team_id, group=group, phase='group')

    if match_date or match_time:
        Match.set_datetime(match_id, match_date, match_time)

    flash('Partita di girone creata con successo.', 'success')
    return redirect(url_for('admin.match_manager'))


# ── Coppa Chiosco ──────────────────────────────────────────────────────────
@admin_bp.route('/coppa-chiosco', methods=['GET'])
@role_required('admin')
def coppa_chiosco_admin():
    teams = Team.get_all()
    teams.sort(key=lambda x: (-(x.get('coppa_chiosco_points') or 0), x.get('name') or ''))
    return render_template('admin/coppa_chiosco.html', teams=teams)


@admin_bp.route('/coppa-chiosco/<team_id>/points', methods=['POST'])
@role_required('admin')
def coppa_chiosco_update_points(team_id):
    from flask import jsonify
    action = request.form.get('action')
    team = Team.get_by_id(team_id)
    if not team:
        return jsonify({'error': 'Squadra non trovata'}), 404

    delta = 1 if action == 'add' else -1
    Team.update_coppa_chiosco_points(team_id, delta)
    updated = Team.get_by_id(team_id)
    new_points = updated.get('coppa_chiosco_points') or 0
    return jsonify({'points': new_points})


# ── Delete Match ───────────────────────────────────────────────────────────
@admin_bp.route('/match-manager/delete/<match_id>', methods=['POST'])
@role_required('admin', 'organizzatore')
def delete_match(match_id):
    match = Match.get_by_id(match_id)
    if not match:
        flash('Partita non trovata.', 'danger')
        return redirect(url_for('admin.match_manager'))

    db.collection(Match.collection_name).document(match_id).delete()
    flash('Partita eliminata con successo.', 'success')
    return redirect(url_for('admin.match_manager'))

