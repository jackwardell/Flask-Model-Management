import os
import warnings
from pathlib import Path

import attr
from wtforms import BooleanField
from wtforms import IntegerField
from wtforms import StringField

# from . import ModelOperation
# from . import Query

THIS_DIR = Path(os.path.dirname(os.path.realpath(__file__)))
TEMPLATES_DIR = THIS_DIR / "templates"

ENDPOINT = "model_management"
URL_PREFIX = "/model-management"

CRUD_OPERATIONS = frozenset({"create", "read", "update", "delete"})

MODEL_TEMPLATE = "model.html.jinja2"
OPERATIONS_FOLDER = "operations/"
TEMPLATE_SUFFIX = ".html.jinja2"

FAILURE_MESSAGE = "danger"
WARNING_MESSAGE = "warning"
SUCCESS_MESSAGE = "success"
INFO_MESSAGE = "primary"


class FieldUI:
    def __init__(self, field):
        self._field = field

    def __call__(self, *args, **kwargs):
        return self._field(*args, **kwargs)

    # def make_field(self, operation):
    #     description = FieldUI.from_column(self)
    #
    #     render_kw = {}
    #     # todo: consider using description everywhere over render_kw?
    #     if self.autoincrement is True and operation == "create":
    #         render_kw["disabled"] = "true"
    #         render_kw["placeholder"] = "AUTOINCREMENT"
    #
    #     if all(
    #         [
    #             self.required,
    #             operation == "create",
    #             "disabled" not in render_kw,
    #             not self.type.is_bool,
    #         ]
    #     ):
    #         render_kw["required"] = "true"
    #
    #     field = self.type.make_wtf_field(
    #         self.name,
    #         default=self.default,
    #         description=description,
    #         render_kw=(render_kw or None),
    #     )
    #     return field

    @classmethod
    def from_column(cls, col):
        if col == int:
            return cls(IntegerField)
        elif col == bool:
            return cls(BooleanField)
        else:
            return cls(StringField)


@attr.s(eq=False)
class ColumnType:
    """A representation of a sqlalchemy column type"""

    python_type = attr.ib()
    sqlalchemy_type = attr.ib()

    @classmethod
    def from_sqlalchemy_col_type(cls, col_type):
        return cls(col_type.python_type, str(col_type))

    def __eq__(self, other):
        return self.python_type is other

    def __str__(self):
        return self.python_type.__name__


@attr.s
class Column:
    """A representation of a sqlalchemy model column"""

    key = attr.ib()
    name = attr.ib()
    type = attr.ib()
    required = attr.ib(default=True)
    default = attr.ib(default=None)
    primary_key = attr.ib(default=False)
    foreign_key = attr.ib(default=False)
    autoincrement = attr.ib(default=False)

    @property
    def nullable(self):
        return not self.required

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


@attr.s
class Model:
    """A representation of a sqlalchemy database model"""

    model = attr.ib()
    excluded_columns = attr.ib(factory=list)
    excluded_operations = attr.ib(factory=list)
    view_decorators = attr.ib(factory=list)

    @property
    def sqlalchemy_model(self):
        return self.model

    @property
    def name(self):
        return str(self.model.__tablename__)

    @property
    def columns(self):
        cols = []
        for col in self.model.__table__.columns:
            if col.name not in self.excluded_columns:
                cols.append(Column.from_sqlalchemy_column(col))

            elif col.name in self.excluded_columns and not col.nullable:
                warnings.warn(
                    f"You have excluded the column: {col.name}. It is a "
                    f"non-nullable column, and therefore required. By excluding "
                    f"it you will not be able to 'create'"
                )

        return cols

    # @property
    # def query(self):
    #     return Query.from_sqlalchemy_model(self.model)

    @classmethod
    def from_sqlalchemy_model(cls, model, **kwargs):
        return cls(model, **kwargs)

    def make_sqlalchemy_model(self, **kwargs):
        return self.model(**kwargs)

    def decorate(self, func):
        for decorator in self.view_decorators:
            func = decorator(func)
        return func

    # def operation(self, operation):
    #     return ModelOperation(operation, self)

    # @property
    # def operations(self):
    #     allowed_operations = CRUD_OPERATIONS - set(self.excluded_operations)
    #     return [self.operation(operation) for operation in allowed_operations]

    @property
    def endpoint(self):
        return self.name

    @property
    def route(self):
        return self.name

    # @property
    # def primary_key(self):
    #     return [c for c in self.columns if c.primary_key].pop()

    # def redirect(self, blueprint):
    #     endpoint = self.operation("read").endpoint_with_blueprint(blueprint)
    #     return lambda: redirect(url_for(endpoint))

    # def all(self):
    #     return self.query.limit(100).all()


class Operation:
    pass
