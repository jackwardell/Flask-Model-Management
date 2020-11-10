from flask_wtf import FlaskForm
from wtforms import SubmitField

from .domain import field_from_column
from .helpers import get_logger


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
        get_logger().info(f"FORM PARAMS: form params output with: {params}")
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
                get_logger().info(f"FORM FIELD: {k}={v}")
                params[self.strip_prefix(k)] = v

        get_logger().info(
            f"FORM LABELLED PARAMS: '{label}' params output with: {params}"
        )
        return params

    def _get_labelled_fields(self, label):
        fields = [
            field
            for field in self
            if field.name not in self.HIDDEN_FIELDS and field.name.startswith(label)
        ]

        get_logger().info(
            f"FORM LABELLED FIELDS: '{label}' fields found: {[f.name for f in fields]}"
        )
        return fields


# @property
# def fields(self):
#     fields = [
#         field
#         for field in self
#         if field.label.text not in self.HIDDEN_FIELDS
#            and not field.name.startswith("query_")
#     ]
#     return fields

# def fields_to_show(self):
#     fields = [
#         field
#         for field in self
#         if field.label.text not in self.HIDDEN_FIELDS
#            and not field.name.startswith("query_")
#     ]
#     return fields

#
# @property
# def params(self):
#     return {}

# @classmethod
# def from_dict(cls, multi_dict):
#     return cls(**multi_dict)


# class FormFactory:
#     def __init__(self, model, operation):
#         self.model = model
#         self.operation = operation
#
#     def make(self, multi_dict):
#
#     def from_request(self, request):
#         multi_dict = request.args if request.method == "GET" else request.form
#         return Form(**multi_dict)
#
#     def make_form(self, multi_dict):
#         return Form(**multi_dict)
#
#     @staticmethod
#     def make_create_form(multi_dict):
#         return Form(**multi_dict)
#
#     @staticmethod
#     def make_read_form(multi_dict):
#         return Form(**multi_dict)
#
#     @staticmethod
#     def make_update_form(multi_dict):
#         return Form(**multi_dict)
#
#     @staticmethod
#     def make_delete_form(multi_dict):
#         return Form(**multi_dict)


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


def get_form(operation, multi_dict):
    form = type(f"{operation.name.title()}Form", (CRUDForm,), {})
    get_logger().info(f"FORM CREATION: {operation.name} form created")

    for column in operation.model.columns:
        protocols = get_protocols(operation.name)
        for protocol in protocols:
            name = protocol + "_" + column.name
            setattr(form, name, field_from_column(column))

    get_logger().info(f"FORM INSTANTIATION: form init called with values: {multi_dict}")
    return form(multi_dict)