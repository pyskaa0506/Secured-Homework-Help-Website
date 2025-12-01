import os

class Config:
    SECRET_KEY = 'mvp-secret-key' # Needed for session management
    # TODO: Change to postgresql
    SQLALCHEMY_DATABASE_URI = 'sqlite:///mvp.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False