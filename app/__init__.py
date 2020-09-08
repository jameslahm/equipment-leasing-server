from flask import Flask,jsonify
from flask_sqlalchemy import SQLAlchemy
from config import config
from flask_migrate import Migrate
import os

db = SQLAlchemy()
migrate = Migrate()

def create_app():
    app = Flask(__name__)

    config_name= os.getenv("FLASK_ENV") or "development"

    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    db.init_app(app)
    migrate.init_app(app,db)

    from .api_1_0 import api as api_1_0_blueprint
    app.register_blueprint(api_1_0_blueprint,url_prefix='/api')
    
    return app