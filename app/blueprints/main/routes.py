from flask import Blueprint, render_template
from app.models import Team, Match, Goal

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
    teams = Team.query.filter_by(group=group).all()
    matches = Match.query.filter_by(group=group, phase='group', played=True).all()

    # ── Build raw stats ──────────────────────────────────────────────
    stats = {}
    for t in teams:
        stats[t.id] = {
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
        h = stats[m.home_team_id]
        a = stats[m.away_team_id]

        h['played'] += 1
        a['played'] += 1
        h['gf'] += m.home_score
        h['ga'] += m.away_score
        a['gf'] += m.away_score
        a['ga'] += m.home_score

        if m.home_score > m.away_score:
            h['wins'] += 1
            h['pts'] += 3
            a['losses'] += 1
        elif m.home_score < m.away_score:
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
    tied_ids = {t['team'].id for t in tied_teams}

    # Build H2H stats
    h2h = {tid: {'pts': 0, 'gd': 0} for tid in tied_ids}

    for m in all_matches:
        if m.home_team_id in tied_ids and m.away_team_id in tied_ids:
            if m.home_score > m.away_score:
                h2h[m.home_team_id]['pts'] += 3
            elif m.home_score < m.away_score:
                h2h[m.away_team_id]['pts'] += 3
            else:
                h2h[m.home_team_id]['pts'] += 1
                h2h[m.away_team_id]['pts'] += 1

            h2h[m.home_team_id]['gd'] += m.home_score - m.away_score
            h2h[m.away_team_id]['gd'] += m.away_score - m.home_score

    # Sort tied teams by H2H pts → H2H gd → overall gd → overall gf
    tied_teams.sort(
        key=lambda s: (
            h2h[s['team'].id]['pts'],
            h2h[s['team'].id]['gd'],
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
    quarters = Match.query.filter_by(phase='quarter').order_by(Match.id).all()
    semis = Match.query.filter_by(phase='semi').order_by(Match.id).all()
    final = Match.query.filter_by(phase='final').first()

    return render_template(
        'public/tournament_tree.html',
        quarters=quarters,
        semis=semis,
        final=final,
    )


@main_bp.route('/group/<group>')
def group_detail(group):
    """Public group detail — standings + all matches."""
    if group not in ('A', 'B', 'C', 'D'):
        return render_template('public/standings.html', groups={}), 404

    standings = get_standings(group)
    matches = Match.query.filter_by(group=group, phase='group')\
                   .order_by(Match.id).all()

    return render_template(
        'public/group_detail.html',
        group=group,
        standings=standings,
        matches=matches,
    )


@main_bp.route('/match/<int:match_id>')
def match_detail_public(match_id):
    """Public match detail — scorers + MVP."""
    match = Match.query.get_or_404(match_id)

    home_goals = Goal.query.filter_by(match_id=match.id, team_id=match.home_team_id)\
                     .order_by(Goal.minute).all()
    away_goals = Goal.query.filter_by(match_id=match.id, team_id=match.away_team_id)\
                     .order_by(Goal.minute).all()

    return render_template(
        'public/match_detail.html',
        match=match,
        home_goals=home_goals,
        away_goals=away_goals,
    )

