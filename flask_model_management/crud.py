import attr
from flask import g

from flask_model_management.helpers import get_session


@attr.s
class CRUDFailure(Exception):
    message = attr.ib()
    model = attr.ib()
    operation = attr.ib()


def get_crud():
    return CRUD(g.model)


@attr.s
class CRUD:
    OPERATIONS = frozenset({"create", "read", "update", "delete"})

    model = attr.ib()

    def operate(self, method, **kwargs):
        return getattr(self, method)(**kwargs)

    def create(self, **kwargs):
        session = get_session()

        model = self.model(**kwargs)
        session.add(model)
        try:
            session.commit()
        except Exception as e:
            session.rollback()
            raise CRUDFailure(str(e), self.model, "create") from e
        return model

    def read(self, **kwargs):
        session = get_session()

        query = session.query(self.model)
        for k, v in kwargs.items():
            query = query.filter_by(**{k: v})
        try:
            result = query.all()
        except Exception as e:
            session.rollback()
            raise CRUDFailure(str(e), self.model, "read") from e
        return result

    def update(self, where: dict, update: dict):
        session = get_session()

        rows = self.read(**where)
        for row in rows:
            for k, v in update.items():
                setattr(row, k, v)
        try:
            session.commit()
        except Exception as e:
            session.rollback()
            raise CRUDFailure(str(e), self.model, "update") from e
        return rows

    def delete(self, **kwargs):
        session = get_session()

        rows = self.read(**kwargs)
        for row in rows:
            session.delete(row)
        try:
            session.commit()
        except Exception as e:
            session.rollback()
            raise CRUDFailure(str(e), self.model, "delete") from e
        return
