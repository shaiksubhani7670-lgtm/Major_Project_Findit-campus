"""
FindIt Campus — Application Configuration
Loads environment variables and provides config classes for different environments.
"""

import os
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables from .env file (parent directory or backend directory)
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))


class Config:
    """Base configuration shared across all environments."""

    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-me')
    DEBUG = False
    TESTING = False

    # Database
    # Checks multiple env var names: DATABASE_URL (manual), POSTGRES_URL_NON_POOLING
    # (Neon serverless-safe), POSTGRES_URL (Neon pooled), then falls back to SQLite.
    _raw_db_url = (
        os.getenv('DATABASE_URL')
        or os.getenv('POSTGRES_URL_NON_POOLING')  # Neon non-pooled (best for serverless)
        or os.getenv('POSTGRES_URL')              # Neon pooled
    )
    if not _raw_db_url:
        bundled_db = os.path.join(os.path.dirname(__file__), 'findit_campus.db')
        if not os.path.exists(bundled_db):
            alt_db = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'findit_campus.db'))
            if os.path.exists(alt_db):
                bundled_db = alt_db

        # On Vercel / serverless (where filesystem is read-only except /tmp)
        if os.getenv('VERCEL') or (os.path.exists('/tmp') and not os.access(os.path.dirname(bundled_db), os.W_OK)):
            import shutil
            tmp_db = '/tmp/findit_campus.db'
            if not os.path.exists(tmp_db) and os.path.exists(bundled_db):
                try:
                    shutil.copy2(bundled_db, tmp_db)
                except Exception as e:
                    print(f"[Config] Error copying database to /tmp: {e}")
            if os.path.exists(tmp_db):
                _raw_db_url = f"sqlite:///{tmp_db}"
            else:
                _raw_db_url = f"sqlite:///{bundled_db}"
        else:
            _raw_db_url = f"sqlite:///{bundled_db}"

    # Neon / Heroku return postgres:// but SQLAlchemy requires postgresql://
    if _raw_db_url.startswith('postgres://'):
        _raw_db_url = _raw_db_url.replace('postgres://', 'postgresql://', 1)
    SQLALCHEMY_DATABASE_URI = _raw_db_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Note: pool_size/pool_recycle are not used for SQLite (DevelopmentConfig overrides this)
    SQLALCHEMY_ENGINE_OPTIONS = {}

    # JWT
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'jwt-secret-change-me')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(
        seconds=int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', 3600))
    )
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(
        seconds=int(os.getenv('JWT_REFRESH_TOKEN_EXPIRES', 2592000))
    )
    JWT_TOKEN_LOCATION = ['headers']
    JWT_HEADER_NAME = 'Authorization'
    JWT_HEADER_TYPE = 'Bearer'

    # Mail
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', 'FindIt Campus <finditcampus@gmail.com>')

    # Cloudinary
    CLOUDINARY_CLOUD_NAME = os.getenv('CLOUDINARY_CLOUD_NAME')
    CLOUDINARY_API_KEY = os.getenv('CLOUDINARY_API_KEY')
    CLOUDINARY_API_SECRET = os.getenv('CLOUDINARY_API_SECRET')

    # Celery (optional — not used on Vercel serverless)
    CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', None)
    CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', None)

    # Redis (optional — not used on Vercel serverless)
    REDIS_URL = os.getenv('REDIS_URL', None)

    # CORS
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:3000').split(',')

    # File Upload
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload
    ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}

    # ML Models
    YOLO_MODEL_PATH = os.getenv('YOLO_MODEL_PATH', 'ml/models/yolov8_findit.pt')
    SENTENCE_MODEL_NAME = os.getenv('SENTENCE_MODEL_NAME', 'all-MiniLM-L6-v2')
    FAISS_INDEX_PATH = os.getenv('FAISS_INDEX_PATH', 'ml/models/faiss_index.bin')

    # Rate Limiting
    RATELIMIT_DEFAULT = "200 per hour"
    RATELIMIT_STORAGE_URI = os.getenv('REDIS_URL', 'memory://')


class DevelopmentConfig(Config):
    """Development environment configuration."""
    DEBUG = True
    SQLALCHEMY_ECHO = False


class TestingConfig(Config):
    """Testing environment configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'postgresql://findit_user:findit_password@localhost:5432/findit_campus_test'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(seconds=5)


class ProductionConfig(Config):
    """Production environment configuration."""
    DEBUG = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 20,
        'pool_recycle': 300,
        'pool_pre_ping': True,
        'max_overflow': 10,
    }


# Configuration map
config_map = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig,
}


def get_config():
    """Return the configuration class based on FLASK_ENV."""
    env = os.getenv('FLASK_ENV', 'development')
    return config_map.get(env, DevelopmentConfig)
