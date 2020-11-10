import os
from pathlib import Path

import attr
from flask import Blueprint
from flask import request

from .domain import Model
from .helpers import get_model_endpoint

ENDPOINT = "model_management"
URL_PREFIX = "/model-management"
APP_NAME = "model_management"

THIS_DIR = Path(os.path.dirname(os.path.realpath(__file__)))
TEMPLATES_DIR = THIS_DIR / "templates"

CRUD_OPERATIONS = frozenset({"create", "read", "update", "delete"})

MODEL_TEMPLATE = "model.html.jinja2"
OPERATIONS_FOLDER = "operations/"
TEMPLATE_SUFFIX = ".html.jinja2"

FAILURE_MESSAGE = "danger"
WARNING_MESSAGE = "warning"
SUCCESS_MESSAGE = "success"
INFO_MESSAGE = "primary"


@attr.s
class ModelManager:
    # set endpoint
    # default is `model_management`
    name = attr.ib(default=APP_NAME)

    # endpoint = attr.ib(default=ENDPOINT)

    # set url_prefix
    # default is `/model-management`
    url_prefix = attr.ib(default=URL_PREFIX)

    # set location for models to be stored
    models = attr.ib(factory=dict)

    # set db object
    db = attr.ib(default=None)

    # if app:
    #     self.init_app(app, db)

    # self.blueprint = self.create_blueprint()

    # def get_url(self, endpoint, **params):
    #     operation = params.pop("operation", "")
    #     extension = "_" + operation if operation else ""
    #     location = self.name + "." + endpoint + extension
    #     return url_for(location, **params)

    # def is_url(self, endpoint):
    #     return self.name + "." + endpoint == request.endpoint

    def is_model(self, model):
        blueprint, endpoint = request.endpoint.split(".")
        model_endpoint = get_model_endpoint(endpoint)
        return self.name == blueprint and model_endpoint == model.endpoint

    def is_model_operation(self, operation):
        blueprint, endpoint = request.endpoint.split(".")
        return self.name == blueprint and endpoint == operation.endpoint

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

        model = Model.from_sqlalchemy_model(model, **params)

        self.models[model.name] = model

    def init_app(self, app, db=None):
        if db:
            self.db = db

        from .app import apply_to_app

        blueprint = apply_to_app(self.create_blueprint())
        app.register_blueprint(blueprint)
        app.extensions["model_management"] = self

    def create_blueprint(self):
        blueprint = Blueprint(
            self.name,
            __name__,
            url_prefix=self.url_prefix,
            template_folder=TEMPLATES_DIR,
        )
        return blueprint
