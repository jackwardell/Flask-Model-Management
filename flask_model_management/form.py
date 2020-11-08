from flask_wtf import FlaskForm
from wtforms import SubmitField

from .domain import FieldUI


class CRUDForm(FlaskForm):
    HIDDEN_FIELDS = ("Confirm", "CSRF Token")

    confirm = SubmitField("Confirm")

    @classmethod
    def make(cls, multi_dict):
        return cls(**multi_dict)

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


def get_form(operation):
    form = type(f"{operation.name.title()}Form", (CRUDForm,), {})
    for column in operation.model.columns:
        setattr(form, column.name, FieldUI.from_column(column))

    return form
