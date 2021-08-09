import os

import pytest

from mood_app import create_app
from mood_app.models import Base


@pytest.fixture(autouse=True, scope="session")
def env():
    env = {"DATABASE_URI": "sqlite://"}
    os.environ.update(env)
    yield
    for key in env:
        os.environ.pop(key)


@pytest.fixture
def app(env):
    app_ = create_app()
    yield app_


@pytest.fixture
def client(app):

    with app.test_client() as client:
        yield client


@pytest.fixture(autouse=True)
def create_tables(app):
    engine = app.session.get_bind()
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
