import attr

from .helpers import get_model
from flask_model_management.helpers import get_session


@attr.s
class CRUDFailure(Exception):
    message = attr.ib()
    model_operation = attr.ib()

    @property
    def model_name(self):
        return self.model_operation.model.name

    @property
    def operation_name(self):
        return self.model_operation.name


def get_crud(tablename):
    model = get_model(tablename)
    return CRUD(model)


@attr.s
class CRUD:
    OPERATIONS = frozenset({"create", "read", "update", "delete"})

    model = attr.ib()

    @property
    def sqlalchemy_model(self):
        return self.model.model

    def __getitem__(self, item):
        return getattr(self, item)

    # def operate(self, method, **kwargs):
    #     return getattr(self, method)(**kwargs)

    # @staticmethod
    # def jsonify(model):
    #     return {col: getattr(model, col) for col in model.__table__.columns.keys()}

    @staticmethod
    def parse_row(row):
        return {k: v for k, v in row.__dict__.items() if k != "_sa_instance_state"}

    # def parse_rows(self, rows):
    #     return [self.parse_row(row) for row in rows]

    def create(self, filter_by):
        session = get_session()

        model = self.sqlalchemy_model(**filter_by)
        session.add(model)
        try:
            session.commit()
        except Exception as e:
            session.rollback()
            raise CRUDFailure(str(e), self.model["create"]) from e

        session.refresh(model)
        result = self.parse_row(model)
        return result

    def read(self, filter_by: dict) -> list:
        session = get_session()
        query = session.query(self.sqlalchemy_model)

        if filter_by:
            for k, v in filter_by.items():
                query = query.filter_by(**{k: v})

        try:
            result = [self.parse_row(r) for r in query]
        except Exception as e:
            session.rollback()
            raise CRUDFailure(str(e), self.model["read"]) from e

        return result

    def update(self, filter_by: dict, update: dict):
        session = get_session()

        rows = self.read(**filter_by)
        for row in rows:
            for k, v in update.items():
                setattr(row, k, v)
        try:
            session.commit()
        except Exception as e:
            session.rollback()
            raise CRUDFailure(str(e), self.model["update"]) from e

        result = [self.parse_row(r) for r in rows]
        return result

    def delete(self, **kwargs):
        session = get_session()

        rows = self.read(**kwargs)
        result = [self.parse_row(r) for r in rows]
        for row in rows:
            session.delete(row)
        try:
            session.commit()
        except Exception as e:
            session.rollback()
            raise CRUDFailure(str(e), self.model["delete"]) from e

        return result
