import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Base configuration"""
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # JWT Configuration
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key-change-in-production')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(seconds=int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', 3600)))
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(seconds=int(os.getenv('JWT_REFRESH_TOKEN_EXPIRES', 2592000)))
    
    # Power BI (commented out - not in use)
    # POWERBI_CLIENT_ID = os.getenv('POWERBI_CLIENT_ID')
    # POWERBI_CLIENT_SECRET = os.getenv('POWERBI_CLIENT_SECRET')
    # POWERBI_TENANT_ID = os.getenv('POWERBI_TENANT_ID')
    # POWERBI_AUTHORITY_URL = os.getenv('POWERBI_AUTHORITY_URL', f'https://login.microsoftonline.com/{POWERBI_TENANT_ID}')
    # POWERBI_SCOPE = os.getenv('POWERBI_SCOPE', 'https://analysis.windows.net/powerbi/api/.default')
    
    # CORS
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:3000').split(',')

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    SQLALCHEMY_ECHO = True

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    SQLALCHEMY_ECHO = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
