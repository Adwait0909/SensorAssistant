import sys
from pathlib import Path
from flask import Flask
from config import Config
from database.models import db
from database.seed import seed_database

def init_db(app: Flask = None):
    """Initialize database tables and run seeding."""
    if app is None:
        app = Flask(__name__)
        app.config.from_object(Config)

    # Ensure database folder exists for SQLite
    if Config.DB_TYPE == "sqlite":
        db_path = Config.SQLITE_DB_PATH
        db_path.parent.mkdir(parents=True, exist_ok=True)

    db.init_app(app)

    with app.app_context():
        print(f"[INFO] Initializing database using engine: {Config.DB_TYPE}...")
        db.create_all()
        seed_database()
        print("[SUCCESS] Database is ready to use!")

if __name__ == "__main__":
    init_db()
