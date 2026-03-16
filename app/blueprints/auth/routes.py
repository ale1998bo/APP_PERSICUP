from functools import wraps
from flask import (
    Blueprint, render_template, redirect, url_for,
    flash, request
)
from flask_login import login_user, logout_user, login_required, current_user
from app.models import User

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


# ── RBAC Decorator ──────────────────────────────────────────────────────────
def role_required(*roles):
    """Custom decorator: restricts access to users with one of the given roles."""
    def decorator(f):
        @wraps(f)
        @login_required
        def wrapped(*args, **kwargs):
            if current_user.role not in roles:
                flash('Non hai i permessi per accedere a questa pagina.', 'danger')
                return redirect(url_for('main.index'))
            return f(*args, **kwargs)
        return wrapped
    return decorator


# ── Login ───────────────────────────────────────────────────────────────────
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        # Usa la logica Firestore
        user = User.get_by_username(username)

        if user and user.check_password(password):
            login_user(user, remember=True)
            flash(f'Benvenuto, {user.username}!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('main.index'))

        flash('Credenziali non valide.', 'danger')

    return render_template('auth/login.html')


# ── Logout ──────────────────────────────────────────────────────────────────
@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Sei stato disconnesso.', 'info')
    return redirect(url_for('main.index'))
