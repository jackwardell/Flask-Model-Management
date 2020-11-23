from flask_wtf import FlaskForm
from wtforms import SubmitField

from .domain import field_from_column


class CRUDForm(FlaskForm):
    HIDDEN_FIELDS = ("confirm", "csrf_token")

    confirm = SubmitField("Confirm")

    @property
    def fields(self):
        return [field for field in self if field.name not in self.HIDDEN_FIELDS]

    @property
    def filter_fields(self):
        return self._get_labelled_fields("filter_")

    @property
    def insert_fields(self):
        return self._get_labelled_fields("insert_")

    @property
    def params(self):
        if self.is_filter and self.is_insert:
            params = self.filter_params, self.insert_params
        elif self.is_filter:
            params = (self.filter_params,)
        elif self.is_insert:
            params = (self.insert_params,)
        else:
            raise ValueError("")

        return params

    @property
    def filter_params(self):
        return self._get_labelled_params("filter_")

    @property
    def insert_params(self):
        return self._get_labelled_params("insert_")

    @property
    def is_filter(self):
        return any([attr.startswith("filter_") for attr in self.data])

    @property
    def is_insert(self):
        return any([attr.startswith("insert_") for attr in self.data])

    @staticmethod
    def strip_prefix(field):
        return field[7:]

    def _get_labelled_params(self, label):
        params = {}
        for k, v in self.data.items():
            if k.startswith(label) and k not in self.HIDDEN_FIELDS and v is not None:
                params[self.strip_prefix(k)] = v

        return params

    def _get_labelled_fields(self, label):
        fields = [
            field
            for field in self
            if field.name not in self.HIDDEN_FIELDS and field.name.startswith(label)
        ]

        return fields


def get_protocols(operation_name):
    if operation_name == "create":
        return ["insert"]
    elif operation_name == "read":
        return ["filter"]
    elif operation_name == "update":
        return ["filter", "insert"]
    elif operation_name == "delete":
        return ["filter"]
    else:
        raise ValueError("must be a crud operation")


def get_form(model, operation, multi_dict):
    form = type(f"{operation.title()}Form", (CRUDForm,), {})

    for column in model.columns:
        protocols = get_protocols(operation)
        for protocol in protocols:
            name = protocol + "_" + column.name
            setattr(form, name, field_from_column(column))

    return form(multi_dict, meta={"csrf": False})
