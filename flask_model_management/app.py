from flask import Blueprint
from flask import current_app
from flask import flash
from flask import g
from flask import jsonify
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from flask_wtf import FlaskForm

from . import get_session

TABLENAME_FIELD = "_sqlalchemy_model_tablename"


class Form(FlaskForm):
    @property
    def params(self):
        return {}

    @classmethod
    def from_dict(cls, multi_dict):
        return cls(**multi_dict)


class FormFactory:
    def __init__(self, model):
        self.model = model

    def from_request(self, request):
        multi_dict = request.args if request.method == "GET" else request.form
        return Form(**multi_dict)

    def make_form(self, multi_dict):
        return Form(**multi_dict)

    @staticmethod
    def make_create_form(multi_dict):
        return Form(**multi_dict)

    @staticmethod
    def make_read_form(multi_dict):
        return Form(**multi_dict)

    @staticmethod
    def make_update_form(multi_dict):
        return Form(**multi_dict)

    @staticmethod
    def make_delete_form(multi_dict):
        return Form(**multi_dict)


class CRUDFailure(Exception):
    def __init__(self, model):
        self.model = model


class CreateFailure(CRUDFailure):
    operation = "create"


class ReadFailure(CRUDFailure):
    operation = "read"


class UpdateFailure(CRUDFailure):
    operation = "update"


class DeleteFailure(CRUDFailure):
    operation = "delete"


def get_model_from_tablename(tablename):
    return current_app.extensions["model_management"].get_model(tablename)


def get_model_operation_url(model, operation):
    endpoint = current_app.extensions["model_management"].endpoint
    location = endpoint + "." + operation + "_view"
    return url_for(location, tablename=model.tablenmae)


def method_to_operation(method):
    """
    >>> method_to_operation('post')
    create
    >>> method_to_operation('get')
    read
    >>> method_to_operation('put')
    update
    >>> method_to_operation('delete')
    delete
    """
    if method.lower() == "post":
        return "create"
    elif method.lower() == "get":
        return "read"
    elif method.lower() == "put":
        return "update"
    elif method.lower() == "delete":
        return "delete"
    else:
        raise ValueError("Invalid HTTP Method")


app = Blueprint("model_management", __name__)


@app.errorhandler(CRUDFailure)
def handle_crud_failure(crud_failure):
    flash(crud_failure)
    url = get_model_operation_url(crud_failure.model, crud_failure.operation)
    return redirect(url)


@app.url_value_preprocessor
def add_model_from_tablename(_, values):
    g.model = get_model_from_tablename(values["tablename"])


def get_form():
    return FormFactory(g.model).from_request(request)


def get_crud():
    return CRUD(g.model)


def get_operation():
    return method_to_operation(request.method)


def get_template(operation):
    return "operations/" + operation + ".html.jinja2"


@app.route("/api/<tablename>", methods=["POST", "GET", "PUT", "DELETE"])
def table_operation_api():
    result = get_crud().operate(get_operation(), **get_form().params)
    return jsonify(result)


@app.route("/<tablename>/<operation>", methods=["GET"])
def table_operation_view(operation):
    form = get_form()
    template = get_template(operation)
    return render_template(template, form=form)


class CRUD:
    OPERATIONS = frozenset({"create", "read", "update", "delete"})

    def __init__(self, model):
        self.model = model

    # @classmethod
    # def operate_from_app_context(cls, **kwargs):
    #     operation = method_to_operation(request.method)
    #     return getattr(cls(g.model), operation)(**kwargs)

    def operate(self, method, **kwargs):
        return getattr(self, method)(**kwargs)

    def create(self, **kwargs):
        session = get_session()

        model = self.model(**kwargs)
        session.add(model)
        try:
            session.commit()
        except Exception as e:
            session.rollback()
            raise CRUDFailure(model) from e
        return model

    def read(self, **kwargs):
        session = get_session()

        query = session.query(self.model)
        for k, v in kwargs.items():
            query = query.filter_by(**{k: v})
        try:
            result = query.all()
        except Exception as e:
            session.rollback()
            raise ReadFailure(e) from e
        return result

    def update(self, where: dict, update: dict):
        session = get_session()

        rows = self.read(**where)
        for row in rows:
            for k, v in update.items():
                setattr(row, k, v)
        try:
            session.commit()
        except Exception as e:
            session.rollback()
            raise UpdateFailure(e) from e
        return rows

    def delete(self, **kwargs):
        session = get_session()

        rows = self.read(**kwargs)
        for row in rows:
            session.delete(row)
        try:
            session.commit()
        except Exception as e:
            session.rollback()
            raise DeleteFailure(e) from e
        return


# class ModelOperationView:
#     def __init__(self, model_operation):
#         self.model_operation = model_operation
#
#     @property
#     def crud(self):
#         return CRUD(self.model_operation.model.sqlalchemy_model)
#
#     @property
#     def form(self):
#         return DefaultForm.from_model_operation(self.model_operation)
#
#     def create(self):
#         if request.method == "POST":
#             form = self.form(request.form)
#             kwargs = {}
#             for col in self.model_operation.model.columns:
#                 kwargs[col.name] = form[col.name].data
#             self.crud.create(**kwargs)
#             flash("entry created", SUCCESS_MESSAGE)
#
#         else:
#             form = self.form(request.args)
#
#         return render_template(
#             self.model_operation.template, form=form, operation=self.model_operation
#         )
#
#     def read(self):
#         form = self.form(request.args)
#         data = self.crud.read(**form.get_fields_passed())
#
#         return render_template(
#             self.model_operation.template,
#             form=form,
#             data=data,
#             operation=self.model_operation,
#         )
#
#     def update(self):
#         if request.method == "POST":
#             form = self.form(request.form)
#
#             self.crud.update(form.get_query_fields_passed(), form.get_fields_passed())
#             flash("entry updated", SUCCESS_MESSAGE)
#
#         else:
#             form = self.form(request.args)
#
#         return render_template(
#             self.model_operation.template, form=form, operation=self.model_operation
#         )
#
#     def delete(self):
#         if request.method == "POST":
#             form = self.form(request.form)
#
#             self.crud.delete(**form.get_fields_passed())
#             flash("entry deleted", SUCCESS_MESSAGE)
#
#         else:
#             form = self.form(request.args)
#
#         return render_template(
#             self.model_operation.template, form=form, operation=self.model_operation
#         )
