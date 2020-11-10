import attr

from .helpers import get_logger
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

    @staticmethod
    def parse_entry(row):
        return {k: v for k, v in row.__dict__.items() if k != "_sa_instance_state"}

    def get_entries(self, session, filter_by: dict):
        query = session.query(self.sqlalchemy_model)
        if filter_by:
            for k, v in filter_by.items():
                query = query.filter_by(**{k: v})

        return query.all()

    def create(self, insert: dict):
        get_logger().info(
            f"CRUD: creating entry in {self.model.name} with params: {insert}"
        )

        session = get_session()

        model = self.sqlalchemy_model(**insert)
        session.add(model)
        try:
            session.commit()
        except Exception as e:
            session.rollback()
            raise CRUDFailure(str(e), self.model["create"]) from e

        session.refresh(model)
        result = self.parse_entry(model)
        return result

    def read(self, filter_by: dict) -> list:
        get_logger().info(
            f"CRUD: reading entries from {self.model.name} with params: {filter_by}"
        )

        session = get_session()
        entries = self.get_entries(session, filter_by)

        try:
            result = [self.parse_entry(e) for e in entries]
        except Exception as e:
            session.rollback()
            raise CRUDFailure(str(e), self.model["read"]) from e

        return result

    def update(self, filter_by: dict, insert: dict) -> list:
        get_logger().info(
            f"CRUD: updating entries from {self.model.name} with params: {filter_by} to {insert}"
        )

        session = get_session()
        entries = self.get_entries(session, filter_by)

        for entry in entries:
            for k, v in insert.items():
                setattr(entry, k, v)
        try:
            session.commit()
            result = [self.parse_entry(e) for e in entries]
        except Exception as e:
            session.rollback()
            raise CRUDFailure(str(e), self.model["update"]) from e

        return result

    def delete(self, filter_by) -> list:
        get_logger().info(
            f"CRUD: deleting entries from {self.model.name} with params: {filter_by}"
        )

        session = get_session()
        entries = self.get_entries(session, filter_by)
        print(f"ENTRIES IS: {entries}")
        if entries:
            for entry in entries:
                session.delete(entry)

        try:
            result = [self.parse_entry(e) for e in entries]
            session.commit()
        except Exception as e:
            session.rollback()
            raise CRUDFailure(str(e), self.model["delete"]) from e

        return result
