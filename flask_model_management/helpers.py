from flask import current_app


def get_logger():
    return type("logger", (), {"info": lambda *args: print(*args)})


def get_session():
    return current_app.extensions["model_management"].db.session


def get_model(tablename):
    return current_app.extensions["model_management"].models[tablename]
