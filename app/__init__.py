from flask import Flask, redirect
from config import config_by_name
from app.extensions import init_firebase, login_manager
from app.storage import get_file_url


def create_app(config_name='dev'):
    """Application Factory — creates and configures the Flask app."""
    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name])

    # ── Extensions ──────────────────────────────────────────────
    init_firebase(app)
    login_manager.init_app(app)

    # ── Blueprints ──────────────────────────────────────────────
    from app.blueprints.auth.routes import auth_bp
    from app.blueprints.admin.routes import admin_bp
    from app.blueprints.main.routes import main_bp
    from app.blueprints.player.routes import player_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(player_bp)

    # ── Serve uploaded files (redirect a GCS) ────────────────────
    @app.route('/uploads/<path:filename>')
    def uploaded_file(filename):
        return redirect(get_file_url(filename))

    return app

