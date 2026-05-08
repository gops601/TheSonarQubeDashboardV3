from flask import Flask
from app.config import Config
from app.services.database import ensure_db_schema
from app.routes.api import api_bp
from app.routes.ui import ui_bp

def create_app():
    app = Flask(__name__, template_folder='../templates')
    app.config.from_object(Config)

    # Initialize the database schema
    with app.app_context():
        ensure_db_schema()

    # Register blueprints
    app.register_blueprint(api_bp)
    app.register_blueprint(ui_bp)

    return app
