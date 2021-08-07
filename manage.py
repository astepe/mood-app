from flask.cli import FlaskGroup

from wsgi import app
from mood_app.models import Base


cli = FlaskGroup(app)


@cli.command("create_tables")
def create_tables():
    engine = app.session.get_bind()
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)


if __name__ == "__main__":
    cli()