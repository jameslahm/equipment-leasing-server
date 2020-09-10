from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from config import config
from flask_migrate import Migrate
import os
from flask_cors import CORS

db = SQLAlchemy()
migrate = Migrate()


def create_app():
    app = Flask(__name__)

    config_name = os.getenv("FLASK_ENV") or "development"

    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    db.init_app(app)
    CORS(app)
    migrate.init_app(app, db, render_as_batch=True)

    from .api import api as api_bp
    app.register_blueprint(api_bp, url_prefix='/api')

    return app
