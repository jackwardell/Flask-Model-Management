from tests.conftest import User
from flask_model_management import API


def test_app(app):
    resp = app.get('/model-management/')
    assert resp.status_code == 200
    assert "hello world" in resp.data.decode()
    # assert False
# def test_api(app):
