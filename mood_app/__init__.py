import os

from flask import Flask, _app_ctx_stack
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker


def create_app() -> Flask:
    """
    Creates a new Flask application,
    registers all routes on that application,
    initializes the sqlalchemy session and stores
    it on the app object

    Returns:
        Flask: The Flask application
    """

    app = Flask(__name__)

    with app.app_context():
        # register all routes
        from . import api

        db_uri = (
            f"postgresql://{os.getenv('POSTGRES_USER')}:"
            f"{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('POSTGRES_HOST')}:"
            f"{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}"
        )

        if os.getenv("DATABASE_URI") is not None:
            db_uri = os.getenv("DATABASE_URI")

        engine = create_engine(db_uri)
        # sessions are scoped to each flask app context
        app.session = scoped_session(
            sessionmaker(bind=engine),
            scopefunc=_app_ctx_stack.__ident_func__
        )

    @app.teardown_appcontext
    def remove_session(*args, **kwargs):
        """
        Ensures that sessions are closed and
        removed each time an app context
        is torn down.
        """
        app.session.remove()

    return app
