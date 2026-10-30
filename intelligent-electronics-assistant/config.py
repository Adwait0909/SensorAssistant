import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent

load_dotenv(BASE_DIR / ".env")

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production-12345")
    
    # Database Configuration
    DB_TYPE = os.environ.get("DB_TYPE", "sqlite").lower()
    
    if DB_TYPE == "mysql":
        DB_USER = os.environ.get("DB_USER", "root")
        DB_PASSWORD = os.environ.get("DB_PASSWORD", "")
        DB_HOST = os.environ.get("DB_HOST", "localhost")
        DB_PORT = os.environ.get("DB_PORT", "3306")
        DB_NAME = os.environ.get("DB_NAME", "electronics_assistant")
        SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    else:
        # Default SQLite
        SQLITE_DB_PATH = BASE_DIR / "database" / "app.db"
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{SQLITE_DB_PATH}"

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Upload settings
    UPLOAD_FOLDER = BASE_DIR / "uploads"
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max limit
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
    
    # LLM Settings (optional)
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", None)

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False
