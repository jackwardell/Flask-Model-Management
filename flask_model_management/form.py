from flask import g
from flask import request
from flask_wtf import FlaskForm


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


def get_form():
    return FormFactory(g.model).from_request(request)
