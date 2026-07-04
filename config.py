import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'super-secret-key-change-in-prod')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB
    GCS_BUCKET_NAME = os.environ.get('GCS_BUCKET_NAME', 'persicup-a49df.firebasestorage.app')
    FIREBASE_PROJECT_ID = os.environ.get('FIREBASE_PROJECT_ID', 'persicup-a49df')


class DevConfig(Config):
    """Development configuration."""
    DEBUG = True


class ProdConfig(Config):
    """Production configuration — GCP."""
    DEBUG = False


config_by_name = {
    'dev': DevConfig,
    'prod': ProdConfig,
}
