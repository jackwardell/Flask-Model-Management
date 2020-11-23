import os
from pathlib import Path

from flask import Blueprint
from flask import current_app
from flask import jsonify
from flask import render_template
from flask import request
from flask import url_for

from .crud import CRUDFailure
from .crud import get_crud
from .domain import Model

URL_PREFIX = "/model-management"
APP_NAME = "model_management"

THIS_DIR = Path(os.path.dirname(os.path.realpath(__file__)))
TEMPLATES_DIR = THIS_DIR / "templates"
STATIC_DIR = THIS_DIR / "static"

EXTENSION = "model_management"


def get_model_manager():
    return current_app.extensions["model_management"]


def get_model(tablename):
    return current_app.extensions["model_management"].models[tablename]


def get_url(endpoint, **params):
    location = get_model_manager().name + "." + endpoint
    return url_for(location, **params)


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
        # excluded_columns: list = None,
        # excluded_operations: list = None,
        # decorators: list = None,
    ):
        # params = {
        #     "excluded_columns": excluded_columns or [],
        #     "excluded_operations": excluded_operations or [],
        #     "view_decorators": decorators or [],
        # }

        model = Model(model)

        self.models[model.name] = model

    def init_app(self, app, db=None):
        if db:
            self.db = db

        assert self.db, (
            "You must pass a flask_sqlalchemy.SQLAlchemy (db) object to either "
            "__init__ or init_app"
        )

        self.setup_app(app)

    def setup_app(self, app):
        blueprint = self.create_blueprint()

        @blueprint.context_processor
        def processors():
            rv = {
                "get_url": get_url,
                "model_manager": get_model_manager(),
            }
            return rv

        @blueprint.errorhandler(CRUDFailure)
        def handle_crud_failure(crud_failure):
            return jsonify(message=crud_failure.message, success=False)

        # have chosen this way to design endpoints as it's most common
        @blueprint.route("/")
        def index():
            return render_template("index.html.jinja2")

        @blueprint.route("/<tablename>/")
        def table(tablename):
            model = get_model(tablename)
            return render_template("table.html.jinja2", model=model)

        @blueprint.route("/<tablename>/<operation>")
        def table_operation(tablename, operation):
            model = get_model(tablename)
            form = model.form(operation, request.args)
            template = "operations/" + operation + ".html.jinja2"
            return render_template(template, model=model, form=form)

        @blueprint.route("/api/<tablename>", methods=["POST"])
        def create(tablename):
            model = get_model(tablename)
            form = model.form("create", request.form)
            if form.validate_on_submit():
                data = get_crud().create_single(model, insert=form.insert_params)
                return jsonify(message=f"{tablename} created", success=True, data=data)
            else:
                return jsonify(message=f"Invalid query fields: {form.errors}", success=False)

        @blueprint.route("/api/<tablename>", methods=["GET"])
        def read(tablename):
            model = get_model(tablename)
            form = model.form("read", request.args)
            if form.validate():
                data = get_crud().read_bulk(model, filter_by=form.filter_params)
                return jsonify(message=f"{tablename} read", success=True, data=data)
            else:
                return jsonify(message=f"Invalid query fields: {form.errors}", success=False)

        @blueprint.route("/api/<tablename>", methods=["PUT"])
        def update(tablename):
            model = get_model(tablename)
            form = model.form("update", request.form)
            if form.validate_on_submit():
                data = get_crud().update_bulk(
                    model, filter_by=form.filter_params, insert=form.insert_params
                )
                return jsonify(message=f"{tablename} updated", success=True, data=data)
            else:
                return jsonify(message=f"Invalid query fields: {form.errors}", success=False)

        @blueprint.route("/api/<tablename>", methods=["DELETE"])
        def delete(tablename):
            model = get_model(tablename)
            form = model.form("delete", request.form)
            if form.validate_on_submit():
                data = get_crud().delete_bulk(model, filter_by=form.filter_params)
                return jsonify(message=f"{tablename} deleted", success=True, data=data)
            else:
                return jsonify(message=f"Invalid query fields: {form.errors}", success=False)

        app.register_blueprint(blueprint)
        app.extensions[EXTENSION] = self

    def create_blueprint(self):
        blueprint = Blueprint(
            self.name,
            __name__,
            url_prefix=self.url_prefix,
            template_folder=TEMPLATES_DIR,
            static_folder=str(STATIC_DIR),
        )
        return blueprint
