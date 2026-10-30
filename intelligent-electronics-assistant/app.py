import os
import sys
import logging
from pathlib import Path
from flask import Flask, jsonify, render_template
from flask_cors import CORS

from config import Config
from database.models import db
from database.seed import seed_database
from routes.auth import auth_bp
from routes.dashboard import dashboard_views
from routes.components import components_bp
from routes.projects import projects_bp
from routes.history import history_bp
from routes.recommendations import recommendations_bp
from routes.build import build_bp
from routes.scanner import scanner_bp
from routes.wiring import wiring_bp
from routes.diagnosis import diagnosis_bp
from routes.chatbot import chatbot_bp

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("ElectronicsAssistant")

def create_app(config_class=Config) -> Flask:
    """Application factory for Intelligent Electronics Project Assistant."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Enable CORS
    CORS(app)

    # Ensure uploads directory exists
    uploads_dir = Path(app.config["UPLOAD_FOLDER"])
    uploads_dir.mkdir(parents=True, exist_ok=True)

    # Ensure database folder exists for SQLite
    if app.config.get("DB_TYPE") == "sqlite":
        db_path = app.config.get("SQLITE_DB_PATH")
        if db_path:
            db_path.parent.mkdir(parents=True, exist_ok=True)

    # Initialize extensions
    db.init_app(app)

    # Auto-initialize and seed database on startup
    with app.app_context():
        try:
            db.create_all()
            seed_database()
        except Exception as e:
            logger.error(f"Database initialization error: {e}")

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_views)
    app.register_blueprint(components_bp)
    app.register_blueprint(projects_bp)
    app.register_blueprint(history_bp)
    app.register_blueprint(recommendations_bp)
    app.register_blueprint(build_bp)
    app.register_blueprint(scanner_bp)
    app.register_blueprint(wiring_bp)
    app.register_blueprint(diagnosis_bp)
    app.register_blueprint(chatbot_bp)

    # Friendly global error handlers (never expose raw Python tracebacks in UI)
    @app.errorhandler(404)
    def handle_404(e):
        return render_template("base.html", error_title="Page Not Found", error_msg="The requested page could not be located."), 404

    @app.errorhandler(500)
    def handle_500(e):
        logger.error(f"Internal server error: {e}")
        return jsonify({
            "status": "error",
            "message": "An internal system error occurred. Technical details have been logged to the server terminal."
        }), 500

    return app

app = create_app()

if __name__ == "__main__":
    logger.info("⚡ Starting Intelligent Electronics Project Assistant...")
    logger.info("📍 URL: http://127.0.0.1:5000")
    app.run(host="127.0.0.1", port=5000, debug=True)
