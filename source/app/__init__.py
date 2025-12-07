from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from config import Config
from datetime import date

db = SQLAlchemy()
login_manager = LoginManager()
# login route inside auth blueprint
login_manager.login_view = 'auth.login'

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)
    limiter.init_app(app)

    # add blueprints
    from app.auth.routes import auth
    from app.main.routes import main
    from app.admin.routes import admin

    app.register_blueprint(auth)
    app.register_blueprint(main)
    app.register_blueprint(admin)

    @app.context_processor
    def inject_now():
        return {'now': date.today()}

    return app