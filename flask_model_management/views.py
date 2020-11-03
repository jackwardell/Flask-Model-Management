from flask import flash
from flask import render_template
from flask import request
from flask_wtf import FlaskForm
from wtforms import HiddenField

from . import CRUD
from . import DefaultForm
from . import SUCCESS_MESSAGE

TABLENAME_FIELD = "_sqlalchemy_model_tablename"


class Form(FlaskForm):
    _sqlalchemy_model_tablename = HiddenField("_sqlalchemy_model_tablename")

    @property
    def params(self):
        return {}


class FormFactory:
    def __init__(self, model, operation):
        self.model = model
        self.operation = operation

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


class ModelOperationView:
    def __init__(self, model_operation):
        self.model_operation = model_operation

    @property
    def crud(self):
        return CRUD(self.model_operation.model.sqlalchemy_model)

    @property
    def form(self):
        return DefaultForm.from_model_operation(self.model_operation)

    def create(self):
        if request.method == "POST":
            form = self.form(request.form)
            kwargs = {}
            for col in self.model_operation.model.columns:
                kwargs[col.name] = form[col.name].data
            self.crud.create(**kwargs)
            flash("entry created", SUCCESS_MESSAGE)

        else:
            form = self.form(request.args)

        return render_template(
            self.model_operation.template, form=form, operation=self.model_operation
        )

    def read(self):
        form = self.form(request.args)
        data = self.crud.read(**form.get_fields_passed())

        return render_template(
            self.model_operation.template,
            form=form,
            data=data,
            operation=self.model_operation,
        )

    def update(self):
        if request.method == "POST":
            form = self.form(request.form)

            self.crud.update(form.get_query_fields_passed(), form.get_fields_passed())
            flash("entry updated", SUCCESS_MESSAGE)

        else:
            form = self.form(request.args)

        return render_template(
            self.model_operation.template, form=form, operation=self.model_operation
        )

    def delete(self):
        if request.method == "POST":
            form = self.form(request.form)

            self.crud.delete(**form.get_fields_passed())
            flash("entry deleted", SUCCESS_MESSAGE)

        else:
            form = self.form(request.args)

        return render_template(
            self.model_operation.template, form=form, operation=self.model_operation
        )
