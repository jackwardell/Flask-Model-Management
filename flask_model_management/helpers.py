from flask import current_app


def get_logger():
    return type("logger", (), {"info": lambda *args: print(*args)})


def get_session():
    return current_app.extensions["model_management"].db.session


def get_model(tablename):
    return current_app.extensions["model_management"].models[tablename]


# def get_model_endpoint(endpoint):
#     """
#     >>> get_model_endpoint("user_create")
#     'user'
#     >>> get_model_endpoint("user_read")
#     'user'
#     >>> get_model_endpoint("user_update")
#     'user'
#     >>> get_model_endpoint("user_delete")
#     'user'
#     >>> get_model_endpoint("user")
#     'user'
#     >>> get_model_endpoint("email_address_delete")
#     'email_address'
#     >>> get_model_endpoint("email_address")
#     'email_address'
#     """
#     operation = endpoint.split("_")[-1]
#     from .crud import CRUD
#
#     if operation in CRUD.OPERATIONS:
#         return "_".join(endpoint.split("_")[:-1])
#     else:
#         return endpoint
