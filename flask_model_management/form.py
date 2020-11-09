from flask_wtf import FlaskForm
from wtforms import SubmitField

from .domain import field_from_column


class CRUDForm(FlaskForm):
    HIDDEN_FIELDS = ("confirm", "csrf_token")

    confirm = SubmitField("Confirm")

    @property
    def fields(self):
        return [field for field in self if field.name not in self.HIDDEN_FIELDS]

    @classmethod
    def make(cls, multi_dict):
        return cls(**multi_dict)

    @property
    def params(self):
        rv = {k: v for k, v in self.data.items() if k not in self.HIDDEN_FIELDS and v}
        return rv

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


def get_form(operation, values):
    form = type(f"{operation.name.title()}Form", (CRUDForm,), {})
    for column in operation.model.columns:

        if operation.name == "create":
            # protocols = "insert"

            setattr(form, column.name, field_from_column(column))

    return form(**values)
