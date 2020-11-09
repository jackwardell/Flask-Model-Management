from flask import current_app
from flask import jsonify
from flask import render_template
from flask import request
from flask import url_for

from .crud import CRUDFailure
from .crud import get_crud
from .form import get_form
from .helpers import get_model
from .helpers import get_operation_name


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


# def get_params(model):
#     params = {}
#     for col in model.__table__.columns:
#         params[col.name] = getattr(model, col.name)
#     return params


# app = Blueprint("model_management", __name__)


# @attr.s
# class APIResponse:
#     code = attr.ib()
#     data = attr.ib()
#
#     @property
#     def ok(self):
#         return str(self.code).startswith("2")
#
#     def serve(self):
#         return jsonify(data=self.data, ok=self.ok), self.code


def create_response(message, status_code, data=None, **kwargs):
    success = str(status_code).startswith("2")
    if data:
        kwargs["data"] = data
    return jsonify(message=message, success=success, **kwargs)


class Endpoints:
    index_view = "index"
    table_view = "table"
    table_operation_view = "table_operation"
    table_api = "table_api"


# def model_to_params(payload):
#     if isinstance(payload, list):
#         return [model_to_params(i) for i in payload]
#     else:
#         return {col: getattr(payload, col) for col in payload.__table__.columns.keys()}


def parse_result(result):
    if isinstance(result, list):
        return [parse_result(i) for i in result]
    else:
        return {col: getattr(result, col) for col in result.__table__.columns.keys()}


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
        # flash("hello")
        # location = get_model_manager().name + "." + Endpoints.table_operation_view

        # url = get_model_operation_url(crud_failure.model, crud_failure.operation)
        # return redirect(url_for(location, tablename=crud_failure.model_name, operation=crud_failure.operation_name))
        # return redirect("/hello")
        return create_response(crud_failure.message, 500)

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
        form = get_form(model[operation], request.args.to_dict())
        template = get_template(operation)
        return render_template(template, model=model, form=form)

    @app.route(
        "/api/<tablename>",
        methods=["POST", "GET", "PUT", "DELETE"],
        endpoint=Endpoints.table_api,
    )
    def table_operation_api(tablename):
        model = get_model(tablename)
        operation = model[get_operation_name()]

        if request.method == "GET":
            request_data = request.args.to_dict()
            statement = f"{tablename} read"
        else:
            request_data = request.form.to_dict()
            statement = f"{tablename} {operation.name}"

        with_params = (
            f'with params: ({", ".join([f"{k}={v}" for k, v in request_data.items()])})'
        )
        message = statement + " " + with_params

        form = get_form(operation, request_data)
        result = get_crud(tablename)[operation.name](form.params)

        return create_response(message, 200, data=result)


def write_message(model_name, operation_name, data):
    return f'{model_name} {operation_name}d with params: ({", ".join([f"{k}={v}" for k, v in data.items()])}) '


class QueryString:
    def __init__(self, string):
        self.string = string
