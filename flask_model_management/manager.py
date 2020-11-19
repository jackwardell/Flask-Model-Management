import os
from pathlib import Path

from flask import Blueprint
from flask import current_app

from .domain import Model

URL_PREFIX = "/model-management"
APP_NAME = "model_management"

THIS_DIR = Path(os.path.dirname(os.path.realpath(__file__)))
TEMPLATES_DIR = THIS_DIR / "templates"
EXTENSION = "model_management"


def get_model_manager():
    return current_app.extensions["model_management"]


class ModelManager:
    def __init__(self, name=None, url_prefix=None, db=None):
        # set endpoint
        # default is `model_management`
        self.name = name or APP_NAME

        # set url_prefix
        # default is `/model-management`
        self.url_prefix = url_prefix or URL_PREFIX

        # set location for models to be stored
        self.models = {}

        # set db object
        self.db = db

    def register_model(
        self,
        model,
        excluded_columns: list = None,
        excluded_operations: list = None,
        decorators: list = None,
    ):
        params = {
            "excluded_columns": excluded_columns or [],
            "excluded_operations": excluded_operations or [],
            "view_decorators": decorators or [],
        }

        model = Model(model, **params)

        self.models[model.name] = model

    def init_app(self, app, db=None):
        if db:
            self.db = db

        assert self.db, (
            "You must pass a flask_sqlalchemy.SQLAlchemy (db) object to either "
            "__init__ or init_app"
        )

        from .app import apply_to_app

        blueprint = apply_to_app(self.create_blueprint())
        app.register_blueprint(blueprint)
        app.extensions[EXTENSION] = self

    def setup_app(self, app):
        blueprint = self.create_blueprint()
        blueprint.context_processor()
        app.register_blueprint(blueprint)

    def create_blueprint(self):
        blueprint = Blueprint(
            self.name,
            __name__,
            url_prefix=self.url_prefix,
            template_folder=TEMPLATES_DIR,
        )
        return blueprint
