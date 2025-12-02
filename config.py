import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'mvp-secret-key-change-me'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'postgresql://user:password@localhost:5432/homework_db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False