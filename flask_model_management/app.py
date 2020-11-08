from flask import current_app
from flask import flash
from flask import jsonify
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for

from .crud import CRUDFailure
from .crud import get_crud
from .form import get_form
from .helpers import get_model
from .helpers import get_model_operation_url
from .helpers import get_operation


def get_template(operation):
    return "operations/" + operation + ".html.jinja2"


def get_model_manager():
    return current_app.extensions["model_management"]


def get_models():
    return get_model_manager().models


def get_url(endpoint, **params):
    location = get_model_manager().name + "." + endpoint
    return url_for(location, **params)


def is_url(endpoint):
    return get_model_manager().name + "." + endpoint == request.endpoint


# def is_model(model):
#     blueprint, endpoint = request.endpoint.split(".")
#     model_endpoint = get_model_endpoint(endpoint)
#
#     return get_model_management().name == blueprint and endpoint == operation.endpoint
#
#     return get_model_management().is_model


def is_model_operation():
    return get_model_manager().is_model_operation


def get_params(model):
    params = {}
    for col in model.__table__.columns:
        params[col.name] = getattr(model, col.name)
    return params


# app = Blueprint("model_management", __name__)


class Endpoints:
    index_view = "index"
    table_view = "table"
    table_operation_view = "table_operation"
    table_api = "table_api"


def apply_to_app(app):
    @app.context_processor
    def processors():
        return {
            "models": get_models(),
            "get_url": get_url,
            # "is_url": is_url,
            # "is_model_operation": is_model_operation,
            # "is_model": is_model,
            # "is_model": lambda *args, **kwargs: "",
            # "get_params": get_params,
            "model_manager": get_model_manager(),
            "endpoints": Endpoints,
        }

    @app.errorhandler(CRUDFailure)
    def handle_crud_failure(crud_failure):
        flash(crud_failure)
        url = get_model_operation_url(crud_failure.model, crud_failure.operation)
        return redirect(url)

    # @app.url_value_preprocessor
    # def add_model_from_tablename(_, values):
    #     tablename = values.get("tablename")
    #     if tablename:
    #         g.model = get_model_from_tablename(values["tablename"])

    @app.route("/", methods=["GET"], endpoint=Endpoints.index_view)
    def index():
        return render_template("index.html.jinja2")

    @app.route("/<tablename>/", methods=["GET"], endpoint=Endpoints.table_view)
    def table_view(tablename):
        model = get_model(tablename)
        return render_template("table.html.jinja2", model=model)

    @app.route(
        "/<tablename>/<operation>",
        methods=["GET"],
        endpoint=Endpoints.table_operation_view,
    )
    def table_operation_view(tablename, operation):
        model = get_model(tablename)
        form = get_form(model[operation]).make(request.args)
        template = get_template(operation)
        return render_template(template, model=model, form=form)

    @app.route(
        "/api/<tablename>",
        methods=["POST", "GET", "PUT", "DELETE"],
        endpoint=Endpoints.table_api,
    )
    def table_operation_api(tablename):
        result = get_crud(tablename).operate(get_operation(), **get_form().params)
        return jsonify(result)

    return app
