from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import config
from flask_migrate import Migrate
import os
from flask_cors import CORS
from sqlalchemy import MetaData

naming_convention = {
    "ix": 'ix_%(column_0_label)s',
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(column_0_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

db = SQLAlchemy(metadata=MetaData(naming_convention=naming_convention))
migrate = Migrate()


def create_app(v="production"):
    app = Flask(__name__)

    config_name = os.getenv("FLASK_ENV") or v

    print(config_name)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    db.init_app(app)
    CORS(app)
    migrate.init_app(app, db, render_as_batch=True)

    from . import db_init
    db_init.init_app(app)

    from .api import api as api_bp
    app.register_blueprint(api_bp, url_prefix='/api')

    return app
