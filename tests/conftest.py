import contextlib
import os
import tempfile

import pytest
from flask import abort
from flask import Flask
from flask import request
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base

from flask_model_management.manager import ModelManager
from tests.models import db
from tests.models import populate

# from flask_sqlalchemy import SQLAlchemy

Base = declarative_base()


def request_decorator(func):
    def decorator(*args, **kwargs):
        if request.args.get("hello") == "world":
            return func(*args, **kwargs)
        else:
            abort(404)

    return decorator


@pytest.fixture(scope="function")
def client_factory(sqlalchemy_url):
    model_manager = ModelManager()

    app = Flask(__name__)
    app.config["SECRET_KEY"] = "hello world"
    app.config["SQLALCHEMY_DATABASE_URI"] = sqlalchemy_url

    db.init_app(app)

    model_manager.init_app(app, db)

    from .models import User, Address, RandomTypeTable

    model_manager.register_model(User)
    model_manager.register_model(Address)
    model_manager.register_model(RandomTypeTable)

    with app.app_context():
        db.create_all()
        populate(db.session)

    return app.test_client()


# def create_app():
#     mgmt = ModelManagement()
#     app = Flask(__name__)
#     app.debug = True
#     app.config["SECRET_KEY"] = "hello world"
#     app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
#     app.config["DEBUG_TB_INTERCEPT_REDIRECTS"] = False
#
#     db.init_app(app)
#     toolbar.init_app(app)
#
#     mgmt.register_model(
#         User, excluded_operations=["create"], decorators=[request_decorator]
#     )
#     mgmt.register_model(Address, excluded_columns=["email_address"])
#
#     mgmt.init_app(app, db=db)
#
#     with app.app_context():
#         db.create_all()
#         populate(db.session)
#
#     return app


@pytest.fixture(scope="function")
def sqlalchemy_url():
    directory, file = tempfile.mkstemp()
    url = "sqlite:///" + file + ".db"
    yield url
    os.close(directory)


@contextlib.contextmanager
def engine_context(url):
    engine = create_engine(url, echo=True)
    yield engine
    engine.dispose()


# @pytest.fixture(scope="function")
# def app():
#     app = create_app()
#     with app.app_context():
#         # db.create_all()
#         yield app.test_client()


# @pytest.fixture(scope="function")
# def app_factory():
#     yield create_app

# @pytest.fixture(scope="function")
# def session():
#     with sqlalchemy_url() as url:
#         from sqlalchemy.orm import sessionmaker
#         with engine_context(url) as engine:
#             Base.metadata.create_all(engine)
#             session = sessionmaker(bind=engine)
#             yield session()
