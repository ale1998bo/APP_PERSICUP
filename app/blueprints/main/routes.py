from datetime import date, datetime, timedelta, timezone
from flask import Blueprint, render_template, abort, jsonify, request
from app.models import Team, Match

main_bp = Blueprint('main', __name__)

_IT_WEEKDAYS = ['Lunedì', 'Martedì', 'Mercoledì', 'Giovedì', 'Venerdì', 'Sabato', 'Domenica']

# Durata stimata di una partita (deve combaciare col seed).
DURATA_PARTITA_MIN = 50

# Ordine canonico delle fasi finali (usato per nominare "Giornate" oltre i gironi).
_PHASE_ORDER = {'Quarti': 1, 'Semifinale': 2, 'Finalina': 3, 'Finale': 4}


_CEST = timezone(timedelta(hours=2))  # UTC+2 (ora italiana estiva) per Cloud Run

def _match_status(match, now=None):
    """Stato di una partita: 'live' | 'played' | 'upcoming'."""
    if match.get('played'):
        return 'played'
    if match.get('live'):
        return 'live'
    return 'upcoming'


def _format_day_it(day_str):
    """'2026-06-21' -> 'Mercoledì 21.06'. Falls back to the raw string on parse error."""
    try:
        d = datetime.strptime(day_str, '%Y-%m-%d').date()
        return f"{_IT_WEEKDAYS[d.weekday()]} {d.strftime('%d.%m')}"
    except (ValueError, TypeError):
        return day_str


def _attach_teams(matches):
    for m in matches:
        m['home_team'] = Team.get_by_id(m['home_team_id']) or {"name": "Sconosciuto"}
        m['away_team'] = Team.get_by_id(m['away_team_id']) or {"name": "Sconosciuto"}
    return matches


def _matches_on(day_str):
    """Return all matches whose match_date == day_str (YYYY-MM-DD), with teams attached."""
    all_m = [m for m in Match.get_all() if m.get('match_date') == day_str]
    all_m.sort(key=lambda m: (m.get('match_time') or '99:99'))
    return _attach_teams(all_m)

# ══════════════════════════════════════════════════════════════════════════════
#  STANDINGS CALCULATION — Punti > H2H > Diff. Reti > Goal Fatti
# ══════════════════════════════════════════════════════════════════════════════

def get_standings(group):
    """
    Calculate group standings with correct tiebreaker ordering:
      1. Points (3W / 1D / 0L)
      2. Head-to-Head record among tied teams
      3. Goal Difference
      4. Goals Scored
    Returns a list of dicts sorted best→worst.
    """
    teams = Team.get_by_group(group)
    all_matches_in_group = Match.get_by_group(group)
    matches = [m for m in all_matches_in_group if m.get('phase') == 'group' and m.get('played')]

    # ── Build raw stats ──────────────────────────────────────────────
    stats = {}
    for t in teams:
        stats[t['id']] = {
            'team': t,
            'played': 0,
            'wins': 0,
            'draws': 0,
            'losses': 0,
            'gf': 0,   # goals for
            'ga': 0,   # goals against
            'gd': 0,   # goal difference
            'pts': 0,
        }

    for m in matches:
        h = stats.get(m['home_team_id'])
        a = stats.get(m['away_team_id'])
        
        if not h or not a: continue

        h['played'] += 1
        a['played'] += 1
        h['gf'] += m.get('home_score', 0)
        h['ga'] += m.get('away_score', 0)
        a['gf'] += m.get('away_score', 0)
        a['ga'] += m.get('home_score', 0)

        if m.get('home_score', 0) > m.get('away_score', 0):
            h['wins'] += 1
            h['pts'] += 3
            a['losses'] += 1
        elif m.get('home_score', 0) < m.get('away_score', 0):
            a['wins'] += 1
            a['pts'] += 3
            h['losses'] += 1
        else:
            h['draws'] += 1
            a['draws'] += 1
            h['pts'] += 1
            a['pts'] += 1

    for s in stats.values():
        s['gd'] = s['gf'] - s['ga']

    table = list(stats.values())

    # ── Sort with H2H tiebreaker ─────────────────────────────────────
    table = _sort_with_h2h(table, matches)
    return table


def _sort_with_h2h(table, matches):
    """
    Sort the standings table. Teams with equal points are resolved via
    Head-to-Head mini-league among the tied group, then GD, then GF.
    """
    # First pass: sort by pts, gd, gf (without H2H)
    table.sort(key=lambda s: (s['pts'], s['gd'], s['gf']), reverse=True)

    # Identify groups of teams with the same points
    result = []
    i = 0
    while i < len(table):
        # Find the extent of teams with identical points
        j = i
        while j < len(table) and table[j]['pts'] == table[i]['pts']:
            j += 1

        tied = table[i:j]

        if len(tied) > 1:
            tied = _resolve_h2h(tied, matches)

        result.extend(tied)
        i = j

    return result


def _resolve_h2h(tied_teams, all_matches):
    """
    Among tied teams (same points), compute a H2H mini-league using
    only the matches between them, then sort by:
      1. H2H points
      2. H2H goal difference
      3. Overall goal difference
      4. Overall goals scored
    """
    tied_ids = {t['team']['id'] for t in tied_teams}

    # Build H2H stats
    h2h = {tid: {'pts': 0, 'gd': 0} for tid in tied_ids}

    for m in all_matches:
        if m['home_team_id'] in tied_ids and m['away_team_id'] in tied_ids:
            if m.get('home_score', 0) > m.get('away_score', 0):
                h2h[m['home_team_id']]['pts'] += 3
            elif m.get('home_score', 0) < m.get('away_score', 0):
                h2h[m['away_team_id']]['pts'] += 3
            else:
                h2h[m['home_team_id']]['pts'] += 1
                h2h[m['away_team_id']]['pts'] += 1

            h2h[m['home_team_id']]['gd'] += m.get('home_score', 0) - m.get('away_score', 0)
            h2h[m['away_team_id']]['gd'] += m.get('away_score', 0) - m.get('home_score', 0)

    # Sort tied teams by H2H pts → H2H gd → overall gd → overall gf
    tied_teams.sort(
        key=lambda s: (
            h2h[s['team']['id']]['pts'],
            h2h[s['team']['id']]['gd'],
            s['gd'],
            s['gf'],
        ),
        reverse=True,
    )

    return tied_teams


# ══════════════════════════════════════════════════════════════════════════════
#  ROUTES
# ══════════════════════════════════════════════════════════════════════════════

@main_bp.route('/')
def index():
    """Landing — hero + LIVE + Partite della giornata (accordion) + Sponsors."""
    now = datetime.now()
    today_str = date.today().isoformat()
    all_matches = Match.get_all()
    _attach_teams(all_matches)

    # Calcola lo stato di ogni partita una sola volta
    for m in all_matches:
        m['status'] = _match_status(m, now)

    # ── LIVE: davvero in corso adesso (start <= now < start + 40 min)
    live_matches = [m for m in all_matches if m['status'] == 'live']
    live_matches.sort(key=lambda m: (m.get('match_time') or '99:99'))

    # ── Partite della giornata: SOLO quelle di OGGI.
    # Numerazione "Giornata N" calcolata sull'ordine cronologico di tutte le date
    # presenti nel DB (cosi` se oggi e` G1, G2 o G3 il titolo riflette il numero reale).
    group_dates = sorted({m['match_date'] for m in all_matches
                          if m.get('phase') == 'group' and m.get('match_date')})
    date_to_giornata_num = {d: i + 1 for i, d in enumerate(group_dates)}

    giornate = []
    if today_str in date_to_giornata_num:
        matches_today = [m for m in all_matches
                         if m.get('phase') == 'group' and m.get('match_date') == today_str]
        matches_today.sort(key=lambda m: (m.get('match_time') or '99:99', m.get('group') or ''))
        giornate.append({
            'key': f'g{date_to_giornata_num[today_str]}',
            'title': f"Giornata {date_to_giornata_num[today_str]}",
            'label': _format_day_it(today_str),
            'date': today_str,
            'matches': matches_today,
            'counts': _count_status(matches_today),
            'is_today': True,
        })

    # Fasi finali (Quarti, Semifinale, Finalina, Finale) -> mostrate solo se oggi.
    playoff_phases = sorted(
        {m['phase'] for m in all_matches if m.get('phase') and m['phase'] != 'group'},
        key=lambda p: _PHASE_ORDER.get(p, 99),
    )
    for phase_name in playoff_phases:
        matches_in_phase = [m for m in all_matches
                            if m.get('phase') == phase_name and m.get('match_date') == today_str]
        if not matches_in_phase:
            continue
        matches_in_phase.sort(key=lambda m: (m.get('match_time') or '99:99'))
        giornate.append({
            'key': f"phase-{phase_name.lower()}",
            'title': phase_name,
            'label': _format_day_it(today_str),
            'date': today_str,
            'matches': matches_in_phase,
            'counts': _count_status(matches_in_phase),
            'is_today': True,
        })

    # Tutto cio` che mostriamo e` di oggi -> default aperto la prima sezione.
    open_key = giornate[0]['key'] if giornate else None

    return render_template(
        'public/landing.html',
        live_matches=live_matches,
        giornate=giornate,
        open_key=open_key,
        hero_img='hero-home',
    )


def _count_status(matches):
    """Conta partite per stato (live/played/upcoming)."""
    counts = {'live': 0, 'played': 0, 'upcoming': 0}
    for m in matches:
        counts[m.get('status', 'upcoming')] += 1
    counts['total'] = len(matches)
    return counts


@main_bp.route('/classifica')
def classifica():
    """Group standings (all 4 groups)."""
    groups = {}
    for g in ['A', 'B', 'C', 'D']:
        groups[g] = get_standings(g)
    return render_template(
        'public/standings.html',
        groups=groups,
        hero_img='hero-classifica',
    )


@main_bp.route('/calendario')
def calendario():
    """Calendar — all matches grouped by date (today + upcoming)."""
    today_str = date.today().isoformat()
    all_matches_full = Match.get_all()
    all_matches = [m for m in all_matches_full if (m.get('match_date') or '') >= today_str]
    _attach_teams(all_matches)

    # Numerazione "Giornata N" basata sull'ordine cronologico di tutte le date
    # delle partite di girone presenti nel DB (anche passate), cosi` se oggi e` G3
    # il titolo resta coerente.
    all_group_dates = sorted({m['match_date'] for m in all_matches_full
                              if m.get('phase') == 'group' and m.get('match_date')})
    date_to_giornata_num = {d: i + 1 for i, d in enumerate(all_group_dates)}

    by_date = {}
    for m in all_matches:
        by_date.setdefault(m['match_date'], []).append(m)
    for d in by_date:
        by_date[d].sort(key=lambda m: (m.get('match_time') or '99:99'))

    days = [
        {
            'date': d,
            'label': _format_day_it(d),
            'matches': by_date[d],
            'giornata_num': date_to_giornata_num.get(d),
            'is_today': d == today_str,
        }
        for d in sorted(by_date.keys())
    ]
    return render_template(
        'public/calendario.html',
        days=days,
        hero_img='hero-calendario',
    )


@main_bp.route('/risultati')
def risultati():
    """Results — live matches at top, then played matches grouped by date (newest first)."""
    all_matches = Match.get_all()
    live_matches = [m for m in all_matches if _match_status(m) == 'live']
    played = [m for m in all_matches if m.get('played')]
    _attach_teams(live_matches)
    _attach_teams(played)

    by_date = {}
    for m in played:
        d = m.get('match_date') or 'Senza data'
        by_date.setdefault(d, []).append(m)
    for d in by_date:
        by_date[d].sort(key=lambda m: (m.get('match_time') or '00:00'), reverse=True)

    sorted_dates = sorted(by_date.keys(), reverse=True)
    days = [
        {'date': d, 'label': _format_day_it(d) if d != 'Senza data' else d, 'matches': by_date[d]}
        for d in sorted_dates
    ]
    return render_template(
        'public/risultati.html',
        days=days,
        live_matches=live_matches,
        hero_img='hero-risultati',
    )


@main_bp.route('/coppa-chiosco')
def coppa_chiosco():
    """Coppa Chiosco — classifica generale per punti assegnati dall'admin."""
    teams = Team.get_all()
    teams.sort(key=lambda x: (-(x.get('coppa_chiosco_points') or 0), x.get('name') or ''))
    return render_template('public/coppa_chiosco.html', teams=teams, hero_img='hero-coppa')


@main_bp.route('/coppa-chiosco/json')
def coppa_chiosco_json():
    """Endpoint JSON per aggiornamento live della classifica Coppa Chiosco."""
    teams = Team.get_all()
    teams.sort(key=lambda x: (-(x.get('coppa_chiosco_points') or 0), x.get('name') or ''))
    return jsonify([
        {'name': t['name'], 'points': t.get('coppa_chiosco_points') or 0}
        for t in teams
    ])


@main_bp.route('/tournament')
def tournament():
    """Knockout stage bracket."""
    matches = Match.get_all()
    
    quarters = sorted([m for m in matches if m.get('phase') == 'Quarti'], key=lambda x: x.get('match_date') or x['id'])
    semis = sorted([m for m in matches if m.get('phase') == 'Semifinale'], key=lambda x: x.get('match_date') or x['id'])
    finals = [m for m in matches if m.get('phase') == 'Finale']
    finalinas = [m for m in matches if m.get('phase') == 'Finalina']
    
    final = finals[0] if finals else None
    finalina = finalinas[0] if finalinas else None

    # Attach teams per frontend rendering
    def attach_teams(m_list):
        for m in m_list:
            if m:
                m['home_team'] = Team.get_by_id(m['home_team_id']) or {"name": "Sconosciuto"}
                m['away_team'] = Team.get_by_id(m['away_team_id']) or {"name": "Sconosciuto"}
        return m_list

    quarters = attach_teams(quarters)
    semis = attach_teams(semis)
    final = attach_teams([final])[0] if final else None
    finalina = attach_teams([finalina])[0] if finalina else None

    return render_template(
        'public/tournament_tree.html',
        quarters=quarters,
        semis=semis,
        final=final,
        finalina=finalina,
    )


@main_bp.route('/group/<group>')
def group_detail(group):
    """Public group detail — standings + all matches."""
    if group not in ('A', 'B', 'C', 'D'):
        return render_template('public/standings.html', groups={}), 404

    now = datetime.now()
    standings = get_standings(group)
    matches_raw = Match.get_by_group(group)
    matches = [m for m in matches_raw if m.get('phase') == 'group']

    for m in matches:
        m['home_team'] = Team.get_by_id(m['home_team_id']) or {"name": "Sconosciuto"}
        m['away_team'] = Team.get_by_id(m['away_team_id']) or {"name": "Sconosciuto"}
        m['status'] = _match_status(m, now)

    matches.sort(key=lambda m: (m.get('match_date') or '9999', m.get('match_time') or '99:99'))

    return render_template(
        'public/group_detail.html',
        group=group,
        standings=standings,
        matches=matches,
    )


@main_bp.route('/match/<match_id>')
def match_detail_public(match_id):
    """Public match detail — scorers + MVP."""
    match = Match.get_by_id(match_id)
    if not match:
        abort(404)
        
    home_team = Team.get_by_id(match['home_team_id']) or {"name": "Sconosciuto", "id": match['home_team_id']}
    away_team = Team.get_by_id(match['away_team_id']) or {"name": "Sconosciuto", "id": match['away_team_id']}
    match['home_team'] = home_team
    match['away_team'] = away_team

    home_goals = sorted([g for g in match.get('goals', []) if g['team_id'] == match['home_team_id']], 
                        key=lambda x: (x.get('minute') or 999))
    away_goals = sorted([g for g in match.get('goals', []) if g['team_id'] == match['away_team_id']], 
                        key=lambda x: (x.get('minute') or 999))

    back = request.args.get('back', '')
    status = _match_status(match)
    return render_template(
        'public/match_detail.html',
        match=match,
        home_goals=home_goals,
        away_goals=away_goals,
        back=back,
        status=status,
    )

