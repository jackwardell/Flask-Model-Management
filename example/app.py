"""use this to test the library locally"""
from flask import Flask
from flask_debugtoolbar import DebugToolbarExtension

from flask_model_management.manager import ModelManager
from tests.models import Address
from tests.models import db
from tests.models import populate
from tests.models import User


def create_app():
    model_manager = ModelManager()
    toolbar = DebugToolbarExtension()

    app = Flask(__name__)
    app.debug = True
    app.config["SECRET_KEY"] = "hello world"
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["DEBUG_TB_INTERCEPT_REDIRECTS"] = False
    app.config["DEBUG_TB_PROFILER_ENABLED"] = True

    db.init_app(app)

    model_manager.register_model(User)
    model_manager.register_model(Address)

    model_manager.init_app(app, db)
    toolbar.init_app(app)

    with app.app_context():
        db.create_all()
        populate(db.session)

    return app
