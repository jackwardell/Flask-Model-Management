"""use this to test the library locally"""
from flask import Flask
from flask_debugtoolbar import DebugToolbarExtension

from flask_model_management import ModelManagement
from tests.models import Address
from tests.models import db
from tests.models import populate
from tests.models import User


def create_app():
    mgmt = ModelManagement()
    toolbar = DebugToolbarExtension()

    app = Flask(__name__)
    app.debug = True
    app.config["SECRET_KEY"] = "hello world"
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["DEBUG_TB_INTERCEPT_REDIRECTS"] = False

    db.init_app(app)
    toolbar.init_app(app)

    mgmt.register_model(User, excluded_operations=["create", "update"])
    mgmt.register_model(Address, excluded_columns=["email_address"])

    mgmt.init_app(app, db=db)

    with app.app_context():
        db.create_all()
        populate(db.session)

    return app
