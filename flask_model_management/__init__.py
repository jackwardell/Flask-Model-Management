import os
from pathlib import Path

from flask import render_template
from flask import request
from flask import url_for
from flask_simpleview import Blueprint
from flask_simpleview import SimpleView
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


class Type:
    def __init__(self, python_type, sqlalchemy_type):
        self.python_type = python_type
        self.sqlalchemy_type = sqlalchemy_type

    @property
    def wtf_field(self):
        if isinstance(self.python_type(), str):
            return StringField
        elif isinstance(self.python_type(), int):
            return IntegerField
        elif isinstance(self.python_type(), bool):
            return BooleanField
        else:
            raise ValueError("No field")

    @classmethod
    def from_col_type(cls, type_):
        return cls(type_.python_type, str(type_))

    def __str__(self):
        _, v, _ = str(self.python_type).split("'")
        return v


class Column:
    def __init__(
        self, key, name, type_, required=True, default=None, primary_key=False
    ):
        self.key = key
        self.name = name
        self.type = type_
        self.required = required
        self.default = default
        self.primary_key = primary_key

    @classmethod
    def from_col(cls, col):
        column = cls(
            col.key,
            col.name,
            Type.from_col_type(col.type),
            required=(not col.nullable),
            default=col.default,
            primary_key=col.primary_key,
        )
        return column

    def field(self):
        label = f"{self.name} [{self.type}]"
        field = self.type.wtf_field(label)
        field.__required__ = self.required
        field.__default__ = self.default
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


class Entity:
    @property
    def route(self):
        raise NotImplementedError()

    @property
    def endpoint(self):
        raise NotImplementedError()

    def dispatch_request(self):
        raise NotImplementedError()


class Operation(Entity):
    def __init__(self, model, operation):
        self.model = model
        self.name = operation

    @property
    def template(self):
        return OPERATIONS_FOLDER + self.name + TEMPLATE_SUFFIX

    @property
    def route(self):
        return self.model.route + "/" + self.name

    @property
    def endpoint(self):
        return self.model.endpoint + "_" + self.name

    def make_form(self, multi_dict):
        form = type("Form", (FlaskForm,), {})

        for col in self.model.columns:
            setattr(form, col.name, col.field())

        setattr(form, "pk", HiddenField("pk"))
        setattr(form, "submit", SubmitField("submit"))

        form.hidden_fields = ["CSRF Token", "submit", "pk"]
        return form(multi_dict)

    # def dispatch_request(self):
    #
    #     pk = request.args.get(request.args.get("pk"))
    #
    #     if request.method == "POST":
    #         params = request.form
    #     else:
    #         params = request.args
    #
    #     form = self.make_form(params)
    #
    #     model = self.model.query.get(pk)
    #
    #     if model:
    #         for column in model.__table__.columns:
    #             setattr(model, column.name, form[column.name].data)
    #
    #     return render_template(
    #         self.template, form=form, model=self.model, operation=self
    #     )

    def make_view(self):
        class View(SimpleView):
            endpoint = self.endpoint
            rule = self.route
            template = self.template

            def get(self_):
                form = self.make_form(request.args)
                return render_template(
                    self.template, form=form, model=self.model, operation=self
                )

            def post(self_):
                form = self.make_form(request.form)

                pk = request.args.get(request.args.get("pk"))
                model = self.model.query.get(pk)

                if model:
                    for column in model.__table__.columns:
                        setattr(model, column.name, form[column.name].data)

                return render_template(
                    self.template, form=form, model=self.model, operation=self
                )

        return View


class Model(Entity):
    def __init__(self, model):
        self.model = model

    @property
    def name(self):
        return self.model.__name__

    @property
    def route(self):
        return str(self.model.__tablename__)

    @property
    def endpoint(self):
        return str(self.model.__tablename__)

    @property
    def columns(self):
        return [Column.from_col(c) for c in self.model.__table__.columns]

    @property
    def operations(self):
        return [Operation(self, op) for op in CRUD_OPERATIONS]

    @property
    def primary_key(self):
        return [c for c in self.columns if c.primary_key].pop()

    @property
    def query(self):
        return self.model.query

    def dispatch_request(self):
        return render_template(MODEL_TEMPLATE, model=self)

    def all(self):
        return [Row.from_row(row) for row in self.model.query.limit(100)]

    def __repr__(self):
        return f"Model(table='{self.model.__tablename__}', columns='{self.columns}')"


class ModelManagement:
    def __init__(self, endpoint=None, url_prefix=None):
        self.endpoint = endpoint or ENDPOINT
        self.url_prefix = url_prefix or URL_PREFIX
        self.models = None

    def get_url(self, endpoint, path="", **params):
        extension = f"_{path}" if path else ""
        return url_for(f"{self.endpoint}.{endpoint}{extension}", **params)

    def is_url(self, endpoint, path=""):
        return self.get_url(endpoint, path=path) == request.path

    def init_app(self, app, models=None):
        if models:
            self.models = [Model(m) for m in models]

        mgmt = self.create_blueprint()

        @mgmt.route("/")
        def index():
            return render_template("index.html.jinja2")

        @mgmt.context_processor
        def processors():
            return {
                "models": self.models,
                "get_url": self.get_url,
                "is_url": self.is_url,
            }

        for model in self.models:
            mgmt.add_url_rule(model.route, model.endpoint, model.dispatch_request)

            for operation in model.operations:
                mgmt.add_view(operation.make_view())
                # mgmt.add_url_rule(
                #     operation.route,
                #     operation.endpoint,
                #     operation.dispatch_request,
                #     methods=("GET", "POST"),
                # )

        app.register_blueprint(mgmt)

    def create_blueprint(self):
        mgmt = Blueprint(
            self.endpoint,
            __name__,
            url_prefix=self.url_prefix,
            template_folder=TEMPLATES_DIR,
        )
        return mgmt
