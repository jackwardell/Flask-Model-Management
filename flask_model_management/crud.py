import attr
from flask import current_app

CRUD_OPERATIONS = ("create", "read", "update", "delete")


def get_logger():
    return current_app.logger


def get_session():
    return current_app.extensions["model_management"].db.session


@attr.s
class CRUDFailure(Exception):
    message = attr.ib()
    operation_name = attr.ib()


def get_crud():
    return CRUDApplication(CRUD)


@attr.s
class CRUD:
    """A service that accepts sqlalchemy models performs crud operations on them"""

    model = attr.ib()

    def get_entries(self, session, filter_by: dict):
        query = session.query(self.model)
        if filter_by:
            for k, v in filter_by.items():
                query = query.filter_by(**{k: v})

        return query.all()

    def create(self, insert: dict):
        session = get_session()

        entry = self.model(**insert)
        session.add(entry)
        try:
            session.commit()
        except Exception as e:
            session.rollback()
            raise CRUDFailure(str(e), "create") from e

        session.refresh(entry)
        return entry

    def read(self, filter_by: dict) -> list:
        session = get_session()

        try:
            result = self.get_entries(session, filter_by)
        except Exception as e:
            session.rollback()
            raise CRUDFailure(str(e), "read") from e

        return result

    def update(self, filter_by: dict, insert: dict) -> list:
        session = get_session()

        entries = self.get_entries(session, filter_by)
        for entry in entries:
            for k, v in insert.items():
                setattr(entry, k, v)
        try:
            session.commit()
        except Exception as e:
            session.rollback()
            raise CRUDFailure(str(e), "update") from e

        return entries

    def delete(self, filter_by) -> list:
        session = get_session()

        entries = self.get_entries(session, filter_by)
        if entries:
            for entry in entries:
                session.delete(entry)

        try:
            session.commit()
        except Exception as e:
            session.rollback()
            raise CRUDFailure(str(e), "delete") from e

        return entries


@attr.s
class CRUDApplication:
    crud = attr.ib()

    @staticmethod
    def parse_entry(row):
        return {
            k: str(v) if v else "NULL" for k, v in row.__dict__.items() if k != "_sa_instance_state"
        }

    def create_single(self, model, insert):
        get_logger().info(f"CRUD APP CREATE: insert: {insert}")
        entry = self.crud(model.model).create(insert)
        result = self.parse_entry(entry)
        get_logger().info(f"CRUD APP CREATE: data output: {result}")
        return result

    def create_bulk(self):
        raise NotImplementedError()

    def read_single(self):
        raise NotImplementedError()

    def read_bulk(self, model, filter_by):
        get_logger().info(f"CRUD APP READ: filter: {filter_by}")
        entries = self.crud(model.model).read(filter_by)
        result = [self.parse_entry(e) for e in entries]
        get_logger().info(f"CRUD APP READ: data output: {result}")
        return result

    def update_single(self):
        raise NotImplementedError()

    def update_bulk(self, model, filter_by, insert):
        get_logger().info(f"CRUD APP UPDATE: filter: {filter_by}, insert: {insert}")
        entries = self.crud(model.model).update(filter_by, insert)
        result = [self.parse_entry(e) for e in entries]
        get_logger().info(f"CRUD APP UPDATE: data output: {result}")
        return result

    def delete_single(self):
        raise NotImplementedError()

    def delete_bulk(self, model, filter_by):
        get_logger().info(f"CRUD APP UPDATE: filter: {filter_by}")
        entries = self.crud(model.model).delete(filter_by)
        result = [self.parse_entry(e) for e in entries]
        get_logger().info(f"CRUD APP UPDATE: data output: {result}")
        return result
