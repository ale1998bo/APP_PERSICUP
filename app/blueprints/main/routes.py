from flask import Blueprint, render_template, abort
from app.models import Team, Match

main_bp = Blueprint('main', __name__)

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
    """Homepage — group standings."""
    groups = {}
    for g in ['A', 'B', 'C', 'D']:
        groups[g] = get_standings(g)
    return render_template('public/standings.html', groups=groups)


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

    standings = get_standings(group)
    matches_raw = Match.get_by_group(group)
    matches = sorted([m for m in matches_raw if m.get('phase') == 'group'], key=lambda x: x['id'])
    
    for m in matches:
        m['home_team'] = Team.get_by_id(m['home_team_id']) or {"name": "Sconosciuto"}
        m['away_team'] = Team.get_by_id(m['away_team_id']) or {"name": "Sconosciuto"}

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

    return render_template(
        'public/match_detail.html',
        match=match,
        home_goals=home_goals,
        away_goals=away_goals,
    )

