from flask import current_app
from flask import jsonify
from flask import render_template
from flask import request
from flask import url_for
from flask.views import MethodView

from .crud import CRUDFailure
from .crud import get_crud
from .form import get_form
from .helpers import get_model


def get_model_manager():
    return current_app.extensions["model_management"]


def get_url(endpoint, **params):
    location = get_model_manager().name + "." + endpoint
    return url_for(location, **params)


class Endpoints:
    index_view = "index"
    table_view = "table"
    table_operation_view = "table_operation"
    table_operation_api = "table_api"


class TableOperationAPI(MethodView):
    @staticmethod
    def post(tablename):
        model = get_model(tablename)
        form = get_form(model, "create", request.form)
        if form.validate_on_submit():
            data = get_crud().create_single(model, insert=form.insert_params)
            return jsonify(message=f"{tablename} created", success=True, data=data)
        else:
            return jsonify(message=f"Invalid query fields: {form.errors}", success=False)

    @staticmethod
    def get(tablename):
        model = get_model(tablename)
        form = get_form(model, "read", request.args)
        if form.validate():
            data = get_crud().read_bulk(model, filter_by=form.filter_params)
            return jsonify(message=f"{tablename} read", success=True, data=data)
        else:
            return jsonify(message=f"Invalid query fields: {form.errors}", success=False)

    @staticmethod
    def put(tablename):
        model = get_model(tablename)
        form = get_form(model, "update", request.form)
        if form.validate_on_submit():
            data = get_crud().update_bulk(
                model, filter_by=form.filter_params, insert=form.insert_params
            )
            return jsonify(message=f"{tablename} updated", success=True, data=data)
        else:
            return jsonify(message=f"Invalid query fields: {form.errors}", success=False)

    @staticmethod
    def delete(tablename):
        model = get_model(tablename)
        form = get_form(model, "delete", request.form)

        if form.validate_on_submit():
            data = get_crud().delete_bulk(model, filter_by=form.filter_params)
            return jsonify(message=f"{tablename} deleted", success=True, data=data)
        else:
            return jsonify(message=f"Invalid query fields: {form.errors}", success=False)


class TableOperationView(MethodView):
    @staticmethod
    def get(tablename, operation):
        model = get_model(tablename)
        form = get_form(model, operation, request.args)
        template = "operations/" + operation + ".html.jinja2"
        return render_template(template, model=model, form=form)


def apply_to_app(app):
    @app.context_processor
    def processors():
        rv = {
            "models": lambda: get_model_manager().models,
            "get_url": get_url,
            "model_manager": get_model_manager(),
            "endpoints": Endpoints,
        }
        return rv

    @app.errorhandler(CRUDFailure)
    def handle_crud_failure(crud_failure):
        return jsonify(message=crud_failure.message, success=False)

    @app.route("/", methods=["GET"], endpoint=Endpoints.index_view)
    def index():
        return render_template("index.html.jinja2")

    @app.route("/<tablename>/", methods=["GET"], endpoint=Endpoints.table_view)
    def table_view(tablename):
        model = get_model(tablename)
        return render_template("table.html.jinja2", model=model)

    app.add_url_rule(
        "/api/<tablename>",
        view_func=TableOperationAPI.as_view(Endpoints.table_operation_api),
        methods=["POST", "GET", "PUT", "DELETE"],
    )

    app.add_url_rule(
        "/<tablename>/<operation>",
        view_func=TableOperationView.as_view(Endpoints.table_operation_view),
        methods=["GET"],
    )

    return app
