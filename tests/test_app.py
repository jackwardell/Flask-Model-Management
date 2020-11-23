import pytest
from flask import Flask

from flask_model_management.domain import CRUD_OPERATIONS
from flask_model_management.manager import ModelManager as ModelManagement
from tests.models import Address
from tests.models import db
from tests.models import populate
from tests.models import User

MODELS_AND_COLUMNS = [
    (model, [col.name for col in model.__table__.columns]) for model in (Address, User)
]


@pytest.fixture(scope="function")
def client_factory(sqlalchemy_url):
    def factory(model=None, **kwargs):
        mgmt = ModelManagement()

        app = Flask(__name__)
        app.config["SECRET_KEY"] = "hello world"
        app.config["SQLALCHEMY_DATABASE_URI"] = sqlalchemy_url

        db.init_app(app)

        if model is not None:
            mgmt.register_model(model, **kwargs)

        mgmt.init_app(app, db=db)

        with app.app_context():
            db.create_all()
            populate(db.session)

        return app.test_client()

    return factory


def test_app(client_factory):
    client = client_factory()
    resp = client.get("/model-management/")
    assert resp.status_code == 200


@pytest.mark.parametrize("operation", CRUD_OPERATIONS)
@pytest.mark.parametrize("models_and_columns", MODELS_AND_COLUMNS)
def test_operation(client_factory, operation, models_and_columns):
    model, columns = models_and_columns

    client = client_factory(model)
    resp = client.get(f"/model-management/{model.__tablename__}/{operation}")
    assert resp.status_code == 200

    for col in columns:
        assert col in resp.data.decode()


# @pytest.mark.parametrize("operation", CRUD_OPERATIONS)
# @pytest.mark.parametrize("models_and_columns", MODELS_AND_COLUMNS)
# def test_operation_excluded(client_factory, operation, models_and_columns):
#     model, columns = models_and_columns
#
#     client = client_factory(model, excluded_operations=[operation])
#     resp = client.get(f"/model-management/{model.__tablename__}/{operation}")
#     assert resp.status_code == 404
#
#     for crud_operation in CRUD_OPERATIONS - {operation}:
#         resp = client.get(f"/model-management/{model.__tablename__}/{crud_operation}")
#         assert resp.status_code == 200


# @pytest.mark.parametrize("operation", CRUD_OPERATIONS)
# @pytest.mark.parametrize("models_and_columns", MODELS_AND_COLUMNS)
# def test_column_excluded(client_factory, operation, models_and_columns):
#     model, columns = models_and_columns
#
#     for col in columns:
#         client = client_factory(model, excluded_columns=[col])
#         resp = client.get(f"/model-management/{model.__tablename__}/{operation}")
#         assert resp.status_code == 200
#
#         assert col not in resp.data.decode()
#         # for c in columns:
#         #     if c != col:
#         #         assert c in resp.data.decode()
