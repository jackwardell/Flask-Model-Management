import os
from pathlib import Path
from flask import Blueprint
from flask import render_template
from flask import request
from flask_wtf import FlaskForm
from wtforms import IntegerField
from wtforms import StringField
from flask import url_for
from flask import request

THIS_DIR = Path(os.path.dirname(os.path.realpath(__file__)))
TEMPLATES_DIR = THIS_DIR / "templates"

ENDPOINT = "model_management"
URL_PREFIX = "/model-management"

CRUD_OPERATIONS = ["create", "read", "update", "delete"]


# class API:
#     def __init__(self, model, session):
#         self.model = model
#         self.session = session
#
#     def get(self):
#         query = self.session.query(self.model)
#         for k, v in request.args.items():
#             query = query.filter_by(**{k: v})
#         return query.all()
#
#     def post(self):
#         model = self.model(**dict(request.args.items()))
#         self.session.add(model)
#         self.session.commit()
#         return model
#
#     def put(self):
#         pass
#
#     def delete(self):
#         pass


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
        else:
            raise ValueError("No field")

    @classmethod
    def from_col_type(cls, type_):
        return cls(type_.python_type, str(type_))


class Column:
    def __init__(self, key, name, type_):
        self.key = key
        self.name = name
        self.type = type_

    @classmethod
    def from_col(cls, col):
        return cls(col.key, col.name, Type.from_col_type(col.type))

    @property
    def field(self):
        return self.type.wtf_field(self.name)

    def __repr__(self):
        return f"Column('{self.name}', key='{self.key}', type='{self.type}')"


class Model:
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

    def all(self):
        return self.model.query.limit(100).all()

    def make_form(self, multi_dict):
        form = type("Form", (FlaskForm,), {})

        for col in self.columns:
            setattr(form, col.name, col.field)

        return form(multi_dict)

    def __repr__(self):
        return f"Model(table='{self.model.__tablename__}', columns='{self.columns}')"


# class CRUD:
#     def __init__(self, model, session):
#         self.model = model
#         self.session = session
#
#     def create(self, **kwargs):
#         model = self.model(**kwargs)
#         self.session.add(model)
#         self.session.commit()
#         return model
#
#     def read(self, **kwargs):
#         query = self.session.query(self.model)
#         for k, v in kwargs.items():
#             query = query.filter(**{k: v})
#         return query
#
#     def update(self, **kwargs):
#         query = self.session.query(self.model)
#         for k, v in kwargs.items():
#             query = query.filter(**{k: v})
#         return query
#
#     def delete(self, **kwargs):
#         return self.read(**kwargs).delete()


class ModelManagement:
    def __init__(self, endpoint=None, url_prefix=None):
        self.endpoint = endpoint or ENDPOINT
        self.url_prefix = url_prefix or URL_PREFIX
        self.models = None

    def get_url(self, endpoint, path=""):
        return url_for(f"{self.endpoint}.{endpoint}") + path

    def is_endpoint(self, endpoint):
        blueprint, view = request.endpoint.split(".")
        return self.endpoint == blueprint and endpoint == view

    def init_app(self, app, models=None):
        if models:
            self.models = [Model(model) for model in models]

        mgmt = self.create_blueprint()

        @mgmt.route("/")
        def index():
            return render_template("index.html.jinja2")

        @mgmt.context_processor
        def processors():
            return {
                "models": self.models,
                "get_url": self.get_url,
                "is_endpoint": self.is_endpoint,
            }

        for model_ in self.models:
            mgmt.add_url_rule(
                model_.route,
                model_.endpoint,
                lambda: render_template("model.html.jinja2", model=model_),
            )

            # for operation in CRUD_OPERATIONS:
            #     route = model.route + "/" + operation
            #     endpoint = model.endpoint + "/" + operation
            #     template = "operations/" + operation + ".html.jinja2"
            #
            #     @mgmt.route(route, endpoint=endpoint)
            #     def operation():
            #         form = model.make_form(request.args)
            #         return render_template(template, form=form)

        app.register_blueprint(mgmt)

    def create_blueprint(self):
        mgmt = Blueprint(
            self.endpoint,
            __name__,
            url_prefix=self.url_prefix,
            template_folder=TEMPLATES_DIR,
        )
        return mgmt
