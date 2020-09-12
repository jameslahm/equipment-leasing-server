from flask import current_app
from flask.cli import with_appcontext
from . import db
import click
from .models import Role, User


def init_app(app):
    app.cli.add_command(init_db_command)


@click.command('init-db')
@with_appcontext
def init_db_command():
    """Clear the existing data and create new tables."""
    # db.create_all()
    Role.insert_roles()
    admin = User(email=current_app.config["FLASK_ADMIN"],
                 password="secure", username="zhangzhi_up", confirmed=True)
    db.session.add(admin)
    db.session.commit()
    click.echo('Initialized the database.')
