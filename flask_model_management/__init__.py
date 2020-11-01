import os
from pathlib import Path

from flask import Blueprint
from flask import current_app
from flask import flash
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from flask_wtf import FlaskForm
from wtforms import BooleanField
from wtforms import HiddenField
from wtforms import IntegerField
from wtforms import StringField
from wtforms import SubmitField

THIS_DIR = Path(os.path.dirname(os.path.realpath(__file__)))
TEMPLATES_DIR = THIS_DIR / "templates"

ENDPOINT = "model_management"
URL_PREFIX = "/model-management"

CRUD_OPERATIONS = ["create", "read", "update", "delete"]

MODEL_TEMPLATE = "model.html.jinja2"
OPERATIONS_FOLDER = "operations/"
TEMPLATE_SUFFIX = ".html.jinja2"

FAILURE_MESSAGE = "danger"
WARNING_MESSAGE = "warning"
SUCCESS_MESSAGE = "success"
INFO_MESSAGE = "primary"


class DefaultForm(FlaskForm):
    HIDDEN_FIELDS = ["pk", "submit", "CSRF Token"]

    pk = HiddenField("pk")
    submit = SubmitField("submit")

    def fields_to_show(self):
        return [f for f in self if f.label.text not in self.HIDDEN_FIELDS]

    def get_fields_passed(self):
        fields = {}
        for field in self.fields_to_show():
            if field.data:
                fields[field.label.field_id] = field.data
        return fields

    @property
    def primary_key_filter(self):
        return {self.pk.data: self[self.pk.data].data}

    @classmethod
    def from_model(cls, model_operation):
        for col in model_operation.model.columns:
            setattr(cls, col.name, col.make_field(model_operation))

        if model_operation == "update":
            cls.pk = StringField
            cls.HIDDEN_FIELDS.remove("pk")

        return cls


class ColumnType:
    def __init__(self, python_type, sqlalchemy_type):
        self.python_type = python_type
        self.sqlalchemy_type = sqlalchemy_type

    @property
    def is_str(self):
        return self.python_type is str

    @property
    def is_bool(self):
        return self.python_type is bool

    @property
    def is_int(self):
        return self.python_type is int

    def make_wtf_field(self, label, **kwargs):
        if self.is_str:
            return StringField(label, **kwargs)
        elif self.is_int:
            return IntegerField(label, **kwargs)
        elif self.is_bool:
            return BooleanField(label, **kwargs)
        else:
            raise ValueError("No field")

    @classmethod
    def from_sqlalchemy_col_type(cls, col_type):
        return cls(col_type.python_type, str(col_type))

    def __str__(self):
        return self.python_type.__name__


def get_session():
    return current_app.extensions["model_management"].db.session


class CRUD:
    def __init__(self, model):
        self.model = model

    def create(self, **kwargs):
        model = self.model(**kwargs)
        session = get_session()
        session.add(model)
        session.commit()
        return model

    def read(self, **kwargs):
        session = get_session()
        query = session.query(self.model)
        for k, v in kwargs.items():
            query = query.filter_by(**{k: v})
        return query.all()

    def update(self, pk, **kwargs):
        session = get_session()
        model = session.query(self.model).get(pk)
        for k, v in kwargs.items():
            setattr(model, k, v)
        session.commit()
        return model

    def delete(self, **kwargs):
        session = get_session()
        query = session.query(self.model)
        for k, v in kwargs.items():
            query = query.filter_by(**{k: v})
        return query.delete()


def make_span(text, category=None):
    attrs = f"class='text-{category}'" if category else ""
    return f"<span {attrs}>[{text}]</span>"


class FieldUI:
    def __init__(
        self, col_type=None, primary_key=False, foreign_key=False, nullable=True
    ):
        self._col_type = col_type
        self._pk = primary_key
        self._fk = foreign_key
        self._not_nullable = not nullable

    @property
    def col_type(self):
        return make_span(self._col_type)

    @property
    def pk(self):
        return make_span("PK", INFO_MESSAGE) if self._pk else ""

    @property
    def fk(self):
        return make_span("FK", INFO_MESSAGE) if self._fk else ""

    @property
    def key(self):
        return self.pk or self.fk

    @property
    def nullable(self):
        return make_span("NOT NULLABLE", FAILURE_MESSAGE) if self._not_nullable else ""

    @classmethod
    def from_column(cls, col):
        ui = cls(
            col_type=str(col.type),
            primary_key=col.primary_key,
            foreign_key=col.foreign_key,
            nullable=col.nullable,
        )
        return ui


class Column:
    def __init__(
        self,
        key,
        name,
        col_type,
        required=True,
        default=None,
        primary_key=False,
        foreign_key=False,
        autoincrement=False,
    ):
        self.key = key
        self.name = name
        self.type = col_type
        self.required = required
        self.default = default
        self.primary_key = primary_key
        self.foreign_key = foreign_key
        self.autoincrement = autoincrement

    @classmethod
    def from_sqlalchemy_column(cls, col):
        column = cls(
            col.key,
            col.name,
            ColumnType.from_sqlalchemy_col_type(col.type),
            required=(not col.nullable),
            default=col.default.arg if col.default is not None else None,
            primary_key=col.primary_key,
            foreign_key=bool(col.foreign_keys),
            autoincrement=col.autoincrement,
        )
        return column

    @property
    def nullable(self):
        return not self.required

    def make_field(self, operation):
        description = FieldUI.from_column(self)

        render_kw = {}
        # todo: consider using description everywhere over render_kw?
        if self.autoincrement is True and operation == "create":
            render_kw["disabled"] = "true"
            render_kw["placeholder"] = "AUTOINCREMENT"

        if all(
            [
                self.required,
                operation == "create",
                "disabled" not in render_kw,
                not self.type.is_bool,
            ]
        ):
            render_kw["required"] = "true"

        field = self.type.make_wtf_field(
            self.name,
            default=self.default,
            description=description,
            render_kw=(render_kw or None),
        )
        return field

    def __repr__(self):
        return f"Column('{self.name}', key='{self.key}', type='{self.type}')"


class Row:
    def __init__(self, **kwargs):
        self.result = kwargs

    def __getattr__(self, item):
        return self.result[item]

    def to_dict(self):
        return self.result

    @classmethod
    def from_row(cls, row):
        kwargs = {}
        for col in row.__table__.columns:
            if col.primary_key is True:
                kwargs["pk"] = col.name
            kwargs[col.name] = getattr(row, col.name)

        return cls(**kwargs)


class ModelOperationView:
    def __init__(self, model_operation):
        self.model_operation = model_operation

    @property
    def crud(self):
        return CRUD(self.model_operation.model.sqlalchemy_model)

    def create(self):
        if request.method == "POST":
            form = self.model_operation.make_form(request.form)
            kwargs = {}
            for col in self.model_operation.model.columns:
                kwargs[col.name] = form[col.name].data
            self.crud.create(**kwargs)
            flash("entry created", SUCCESS_MESSAGE)

        else:
            form = self.model_operation.make_form(request.args)

        return render_template(
            self.model_operation.template, form=form, operation=self.model_operation
        )

    def read(self):
        form = self.model_operation.make_form(request.args)
        data = self.crud.read(**form.get_fields_passed())

        return render_template(
            self.model_operation.template,
            form=form,
            data=data,
            operation=self.model_operation,
        )

    def update(self):
        if request.method == "POST":
            form = self.model_operation.make_form(request.form)

            self.crud.update(form.primary_key, **form.get_fields_passed())
            flash("entry updated", SUCCESS_MESSAGE)

        else:
            form = self.model_operation.make_form(request.args)

        return render_template(
            self.model_operation.template, form=form, operation=self.model_operation
        )

    def delete(self):
        return


class ModelOperation:
    def __init__(self, operation, model):
        self.model = model
        self.operation = operation

    @property
    def name(self):
        return self.operation

    @property
    def template(self):
        return OPERATIONS_FOLDER + self.operation + TEMPLATE_SUFFIX

    @property
    def route(self):
        return self.model.name + "/" + self.operation

    @property
    def endpoint(self):
        return self.model.name + "_" + self.operation

    def __str__(self):
        return self.operation

    def __eq__(self, other):
        return str(self).lower() == str(other).lower()

    def make_form(self, multi_dict):
        return DefaultForm.from_model(self)(multi_dict)

    @property
    def view(self):
        return ModelOperationView(self)

    def dispatch_request(self):
        return getattr(self.view, self.operation)()

    def endpoint_with_blueprint(self, blueprint):
        return blueprint + "." + self.endpoint


class Query:
    def __init__(self, get_query):
        self.get_query = get_query

    def __call__(self, *args, **kwargs):
        return self.get_query()

    def __getattr__(self, item):
        return getattr(self(), item)

    @classmethod
    def from_sqlalchemy_model(cls, model):
        return cls(lambda: model.query)


# class Session:
#     def __init__(self, session):
#         self._session = session
#
#     def __call__(self, *args, **kwargs):
#         if not self._session:
#             self._session = self.get_session()
#         return self._session
#
#     def __getattr__(self, item):
#         return getattr(self(), item)
#
#     @classmethod
#     def from_get_session(cls, session):
#         return cls(get_session=session)
#
#     @classmethod
#     def from_db_session(cls, session):
#         return cls(session=session)


class Model:
    def __init__(self, model):
        self._model = model

    @property
    def sqlalchemy_model(self):
        return self._model

    @property
    def name(self):
        return str(self._model.__tablename__)

    @property
    def columns(self):
        cols = [
            Column.from_sqlalchemy_column(col) for col in self._model.__table__.columns
        ]
        return cols

    @property
    def query(self):
        return Query.from_sqlalchemy_model(self._model)

    @classmethod
    def from_sqlalchemy_model(cls, model):
        return cls(model)

    def make_sqlalchemy_model(self, **kwargs):
        return self._model(**kwargs)

    @property
    def create(self):
        return ModelOperation("create", self)

    @property
    def read(self):
        return ModelOperation("read", self)

    @property
    def update(self):
        return ModelOperation("update", self)

    @property
    def delete(self):
        return ModelOperation("delete", self)

    @property
    def operations(self):
        return [self.create, self.read, self.update, self.delete]

    @property
    def endpoint(self):
        return self.name

    @property
    def route(self):
        return self.name

    @property
    def primary_key(self):
        return [c for c in self.columns if c.primary_key].pop()

    def redirect(self, blueprint):
        endpoint = self.read.endpoint_with_blueprint(blueprint)
        return lambda: redirect(url_for(endpoint))

    def all(self):
        return [Row.from_row(row) for row in self.query.limit(100)]

    def __repr__(self):
        return f"Model(table='{self.name}', columns='{self.columns}')"


def get_model_endpoint(endpoint):
    """
    >>> get_model_endpoint("user_create")
    'user'
    >>> get_model_endpoint("user_read")
    'user'
    >>> get_model_endpoint("user_update")
    'user'
    >>> get_model_endpoint("user_delete")
    'user'
    >>> get_model_endpoint("user")
    'user'
    >>> get_model_endpoint("email_address_delete")
    'email_address'
    >>> get_model_endpoint("email_address")
    'email_address'
    """
    operation = endpoint.split("_")[-1]
    if operation in CRUD_OPERATIONS:
        return "_".join(endpoint.split("_")[:-1])
    else:
        return endpoint


#
# class _ModelMgmtState:
#     def __init__(self, mgmt):
#         self.mgmt = mgmt

#
# def pretty_model(model):
#     attrs = ", ".join(
#         [
#             f"{k}={getattr(model, k)}"
#             for k in model.__dir__()
#             if k in model.__table__.columns
#         ]
#     )
#     rv = f"<{model.__class__.__name__}({attrs})>"
#     return rv


class ModelManagement:
    def __init__(self, app=None, endpoint=None, url_prefix=None, db=None):
        # set endpoint
        # default is `model_management`
        self.endpoint = endpoint or ENDPOINT

        # set url_prefix
        # default is `/model-management`
        self.url_prefix = url_prefix or URL_PREFIX

        # set location for models to be stored
        self.models = None

        # set db object
        self.db = None

        if app:
            self.init_app(app, db)

    def get_url(self, endpoint, **params):
        operation = params.pop("operation", "")
        extension = "_" + operation if operation else ""
        location = self.endpoint + "." + endpoint + extension
        return url_for(location, **params)

    def is_url(self, endpoint):
        return self.endpoint + "." + endpoint == request.endpoint

    def is_model(self, model):
        blueprint, endpoint = request.endpoint.split(".")
        model_endpoint = get_model_endpoint(endpoint)
        return self.endpoint == blueprint and model_endpoint == model.endpoint

    def is_model_operation(self, operation):
        blueprint, endpoint = request.endpoint.split(".")
        return self.endpoint == blueprint and endpoint == operation.endpoint

    def init_app(self, app, models=None, db=None):
        self.models = [Model.from_sqlalchemy_model(model) for model in models]

        if db:
            self.db = db

        mgmt = self.create_blueprint()

        mgmt.add_url_rule("/", "index", lambda: render_template("index.html.jinja2"))

        @mgmt.context_processor
        def processors():
            return {
                "models": self.models,
                "get_url": self.get_url,
                "is_url": self.is_url,
                "is_model_operation": self.is_model_operation,
                "is_model": self.is_model,
            }

        for model in self.models:
            mgmt.add_url_rule(model.name, model.name, model.redirect(self.endpoint))

            for operation in model.operations:
                mgmt.add_url_rule(
                    operation.route,
                    operation.endpoint,
                    operation.dispatch_request,
                    methods=("GET", "POST"),
                )

        app.register_blueprint(mgmt)

        app.extensions["model_management"] = self

    def create_blueprint(self):
        mgmt = Blueprint(
            self.endpoint,
            __name__,
            url_prefix=self.url_prefix,
            template_folder=TEMPLATES_DIR,
        )
        return mgmt


if __name__ == "__main__":
    import doctest

    doctest.testmod()
