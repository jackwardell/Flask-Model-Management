import http

from flask import current_app
from flask import jsonify
from flask import render_template
from flask import request
from flask import url_for
from flask.views import MethodView

from .crud import CRUD
from .crud import CRUDApplication
from .crud import CRUDFailure
from .crud import get_crud
from .form import get_form
from .helpers import get_logger
from .helpers import get_model


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
    http_code = http.HTTPStatus(status_code)
    success = str(status_code).startswith("2")
    if data:
        kwargs["data"] = data
    return jsonify(
        message=message,
        success=success,
        status_code=status_code,
        phrase=http_code.phrase,
        description=http_code.description,
        **kwargs,
    )


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
    crud = CRUDApplication(CRUD)

    @app.context_processor
    def processors():
        return {
            "models": get_models(),
            "get_url": get_url,
            "model_manager": get_model_manager(),
            "endpoints": Endpoints,
        }

    @app.errorhandler(CRUDFailure)
    def handle_crud_failure(crud_failure):
        return create_response(crud_failure.message, 500)

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

    class TableAPI(MethodView):
        @staticmethod
        def data(multi_dict):
            return f'({", ".join([f"{k}={v}" for k, v in multi_dict.items()])})'

        def post(self, tablename):
            model = get_model(tablename)
            form = get_form(model["create"], request.form)

            if form.validate_on_submit():

                result = crud.create_single(model, *form.params)

                # result = get_crud(tablename)["create"](*form.params)
                message = f"{tablename} created with params: {self.data(request.form)}"
                return create_response(message, 200, data=result)

            else:
                return create_response("Invalid query fields", 400)

        def get(self, tablename):
            model = get_model(tablename)
            form = get_form(model["read"], request.args)

            if form.validate():
                result = get_crud(tablename)["read"](*form.params)
                message = f"{tablename} read with params: {self.data(form.data)}"
                get_logger().info(f"API: {message}")
                return create_response(message, 200, data=result)

            else:
                return create_response(form.errors, 400)

        def update(self, tablename):
            model = get_model(tablename)
            form = get_form(model["update"], request.form)

            if form.validate_on_submit():
                result = get_crud(tablename)["update"](*form.params)
                message = f"{tablename} updated with params: {self.data(request.form)}"
                get_logger().info(f"API: {message}")
                return create_response(message, 200, data=result)

            else:
                return create_response("Invalid query fields", 400)

        def delete(self, tablename):
            model = get_model(tablename)
            form = get_form(model["delete"], request.form)

            if form.validate():
                result = get_crud(tablename)["delete"](*form.params)
                message = (
                    f"{tablename} deleted from where params: {self.data(request.form)}"
                )
                get_logger().info(f"API: {message}")
                return create_response(message, 200, data=result)

            else:
                return create_response("Invalid query fields", 400)

    # @app.route(
    #     "/api/<tablename>",
    #     methods=["POST", "GET", "PUT", "DELETE"],
    #     endpoint=Endpoints.table_api,
    # )
    # def table_operation_api(tablename):
    #     model = get_model(tablename)
    #     operation = model[get_operation_name()]
    #
    #     if request.method == "GET":
    #         request_data = request.args.to_dict()
    #         statement = f"{tablename} read"
    #     else:
    #         request_data = request.form.to_dict()
    #         statement = f"{tablename} {operation.name}"
    #
    #     get_logger().info(f"API: {request.method} request with data: {request_data}")
    #
    #     with_params = (
    #         f'with params: ({", ".join([f"{k}={v}" for k, v in request_data.items()])})'
    #     )
    #     message = statement + " " + with_params
    #
    #     form = get_form(operation, request_data)
    #     form.validate_on_submit
    #     result = get_crud(tablename)[operation.name](*form.params)
    #
    #     response = create_response(message, 200, data=result)
    #
    #     get_logger().info(
    #         f"API: {request.method} request returned with: {response.json}"
    #     )
    #     return response

    app.add_url_rule(
        "/api/<tablename>",
        view_func=TableAPI.as_view(Endpoints.table_api),
        methods=["POST", "GET", "UPDATE", "DELETE"],
    )

    return app


def write_message(model_name, operation_name, data):
    return f'{model_name} {operation_name}d with params: ({", ".join([f"{k}={v}" for k, v in data.items()])}) '
