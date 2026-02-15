import os
from flask import Flask, send_from_directory
from config import config_by_name
from app.extensions import db, login_manager


def create_app(config_name='dev'):
    """Application Factory — creates and configures the Flask app."""
    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name])

    # ── Upload folder ──────────────────────────────────────────────
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # ── Extensions ──────────────────────────────────────────────
    db.init_app(app)
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

    # ── Serve uploaded files ───────────────────────────────────────
    @app.route('/uploads/<path:filename>')
    def uploaded_file(filename):
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

    # ── Database ────────────────────────────────────────────────
    with app.app_context():
        from app import models  # noqa: F401 – ensure models are registered
        db.create_all()

    return app

