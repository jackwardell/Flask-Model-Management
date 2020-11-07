from flask import current_app
from flask import flash
from flask import g
from flask import jsonify
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for

from .crud import CRUDFailure
from .crud import get_crud
from .form import get_form
from .helpers import get_model_from_tablename
from .helpers import get_model_operation_url
from .helpers import get_operation


def get_template(operation):
    return "operations/" + operation + ".html.jinja2"


def get_model_management():
    return current_app.extensions["model_management"]


def get_models():
    return get_model_management().models


def get_url(endpoint, **params):
    location = get_model_management().name + "." + endpoint
    return url_for(location, **params)


def is_url(endpoint):
    return get_model_management().name + "." + endpoint == request.endpoint


# def is_model(model):
#     blueprint, endpoint = request.endpoint.split(".")
#     model_endpoint = get_model_endpoint(endpoint)
#
#     return get_model_management().name == blueprint and endpoint == operation.endpoint
#
#     return get_model_management().is_model


def is_model_operation():
    return get_model_management().is_model_operation


def get_params(model):
    params = {}
    for col in model.__table__.columns:
        params[col.name] = getattr(model, col.name)
    return params


# app = Blueprint("model_management", __name__)


def apply_to_app(app):
    @app.context_processor
    def processors():
        return {
            "models": get_models(),
            "get_url": get_url,
            "is_url": is_url,
            "is_model_operation": is_model_operation,
            # "is_model": is_model,
            # "is_model": lambda *args, **kwargs: "",
            "get_params": get_params,
        }

    @app.errorhandler(CRUDFailure)
    def handle_crud_failure(crud_failure):
        flash(crud_failure)
        url = get_model_operation_url(crud_failure.model, crud_failure.operation)
        return redirect(url)

    @app.url_value_preprocessor
    def add_model_from_tablename(_, values):
        tablename = values.get("tablename")
        if tablename:
            g.model = get_model_from_tablename(values["tablename"])

    @app.route("/", methods=["GET"])
    def index():
        return render_template("index.html.jinja2")

    @app.route("/<tablename>/<operation>", methods=["GET"])
    def table_operation_view(operation):
        form = get_form()
        template = get_template(operation)
        return render_template(template, form=form)

    @app.route("/<tablename>/", methods=["GET"])
    def table_view():
        return "he"

    @app.route("/api/<tablename>", methods=["POST", "GET", "PUT", "DELETE"])
    def table_operation_api():
        result = get_crud().operate(get_operation(), **get_form().params)
        return jsonify(result)

    return app
