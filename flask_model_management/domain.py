import os
import warnings
from datetime import date
from datetime import datetime
from decimal import Decimal
from functools import partial
from pathlib import Path

import attr
from wtforms import DecimalField
from wtforms import FloatField
from wtforms import IntegerField
from wtforms import StringField
from wtforms.fields import DateField
from wtforms.fields import DateTimeField
from wtforms.fields import RadioField

THIS_DIR = Path(os.path.dirname(os.path.realpath(__file__)))
TEMPLATES_DIR = THIS_DIR / "templates"

ENDPOINT = "model_management"
URL_PREFIX = "/model-management"

CRUD_OPERATIONS = ("create", "read", "update", "delete")

MODEL_TEMPLATE = "model.html.jinja2"
OPERATIONS_FOLDER = "operations/"
TEMPLATE_SUFFIX = ".html.jinja2"


def true_false_or_none(value):
    if value.lower() == "true":
        return True
    elif value.lower() == "false":
        return False
    else:
        return None


def field_from_column(column):
    if column.type == int:
        field = IntegerField
    elif column.type == bool:
        field = partial(
            RadioField,
            coerce=true_false_or_none,
            choices=(("true", "True"), ("false", "False"), ("none", "None")),
        )
    elif column.type == float:
        field = FloatField
    elif column.type == Decimal:
        field = DecimalField
    elif column.type == datetime:
        field = DateTimeField
    elif column.type == date:
        field = DateField
    else:
        field = partial(StringField, filters=[lambda x: x or None])
    return field(column.name)


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
    def is_key(self):
        return self.primary_key or self.foreign_key

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
    callbacks = attr.ib(factory=list)

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

    @property
    def allowed_operations(self):
        allowed_operations = [
            operation for operation in CRUD_OPERATIONS if operation not in self.excluded_operations
        ]
        return allowed_operations

    @property
    def operations(self):
        operations = [ModelOperation(operation, self) for operation in self.allowed_operations]
        return operations

    # @property
    # def primary_key(self):
    #     return [c for c in self.columns if c.primary_key].pop()


@attr.s
class ModelOperation:
    name = attr.ib()
    model = attr.ib()
