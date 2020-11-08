from flask import current_app
from flask import request
from flask import url_for


def get_session():
    return current_app.extensions["model_management"].db.session


def get_model(tablename):
    return current_app.extensions["model_management"].models[tablename]


def get_model_operation_url(model, operation):
    endpoint = current_app.extensions["model_management"].endpoint
    location = endpoint + "." + operation + "_view"
    return url_for(location, tablename=model.tablenmae)


def method_to_operation(method):
    """
    >>> method_to_operation('post')
    create
    >>> method_to_operation('get')
    read
    >>> method_to_operation('put')
    update
    >>> method_to_operation('delete')
    delete
    """
    if method.lower() == "post":
        return "create"
    elif method.lower() == "get":
        return "read"
    elif method.lower() == "put":
        return "update"
    elif method.lower() == "delete":
        return "delete"
    else:
        raise ValueError("Invalid HTTP Method")


def get_operation():
    return method_to_operation(request.method)


def get_model_endpoint(endpoint):
    """
    >>> get_model_endpoint("user_create")
    'user'
    >>> get_model_endpoint("user_read")
    'user'
    >>> get_model_endpoint("user_update")
    'user'
    >>> get_model_endpoint("user_delete")
    'user'
    >>> get_model_endpoint("user")
    'user'
    >>> get_model_endpoint("email_address_delete")
    'email_address'
    >>> get_model_endpoint("email_address")
    'email_address'
    """
    operation = endpoint.split("_")[-1]
    from .crud import CRUD

    if operation in CRUD.OPERATIONS:
        return "_".join(endpoint.split("_")[:-1])
    else:
        return endpoint
