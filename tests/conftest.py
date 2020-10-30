import contextlib
import os
import tempfile
from flask_debugtoolbar import DebugToolbarExtension

import pytest
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

from flask_model_management import ModelManagement

db = SQLAlchemy()
toolbar = DebugToolbarExtension()

Base = declarative_base()

USERS = [
    ("hello", "world", "hello.world@mail.com"),
    ("goodbye", "world", "gb@aol.com"),
    ("another", "person", "lol@gg.co"),
]


# class Plugin:
#     def __init__(self, module):
#         self.module = module
#
#     @property
#     def base(self):
#         return db.Model
#
#     def __getattr__(self, item):
#         return getattr(self.module, item)


# plugin = Plugin(db)


class User(db.Model):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, autoincrement=True)
    first_name = Column(String)
    last_name = Column(String)

    addresses = relationship("Address", back_populates="user")

    def __repr__(self):
        return f"<User('{self.first_name} {self.last_name}')>"


class Address(db.Model):
    __tablename__ = "address"

    id = Column(Integer, primary_key=True)
    email_address = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey("user.id"))

    user = relationship("User", back_populates="addresses")

    def __repr__(self):
        return f"<Address('{self.user}', email_address='{self.email_address}')>"


def populate(session):
    for user_id, (first_name, last_name, email_address) in enumerate(USERS):
        session.add(User(first_name=first_name, last_name=last_name))
        session.add(Address(user_id=user_id, email_address=email_address))
    session.commit()


def create_app():
    mgmt = ModelManagement()

    app = Flask(__name__)
    app.debug = True
    app.config["SECRET_KEY"] = "hello world"
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"

    db.init_app(app)
    toolbar.init_app(app)
    mgmt.init_app(app, models=[User, Address])

    with app.app_context():
        db.create_all()
        populate(db.session)

    return app


@contextlib.contextmanager
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
#     with sqlalchemy_url() as url:
#         app = create_app()
#         with app.app_context():
#             db.create_all()
#             yield app.test_client()

# @pytest.fixture(scope="function")
# def session():
#     with sqlalchemy_url() as url:
#         from sqlalchemy.orm import sessionmaker
#         with engine_context(url) as engine:
#             Base.metadata.create_all(engine)
#             session = sessionmaker(bind=engine)
#             yield session()
