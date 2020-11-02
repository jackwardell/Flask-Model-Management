from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy.orm import relationship

db = SQLAlchemy()

USERS = [
    ("hello", "world", True, "hello.world@mail.com"),
    ("goodbye", "world", False, "gb@aol.com"),
    ("another", "person", False, "lol@gg.co"),
]


class User(db.Model):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    first_name = Column(String)
    last_name = Column(String)
    is_admin = Column(Boolean, default=False, nullable=False)

    addresses = relationship("Address", back_populates="user")

    def __repr__(self):
        return f"<User('{self.first_name} {self.last_name}')>"


class Address(db.Model):
    __tablename__ = "address"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email_address = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey("user.id"))

    user = relationship("User", back_populates="addresses")

    def __repr__(self):
        return f"<Address('{self.user}', email_address='{self.email_address}')>"


def populate(session):
    for user_id, (first_name, last_name, is_admin, email_address) in enumerate(USERS):
        session.add(User(first_name=first_name, last_name=last_name, is_admin=is_admin))
        session.add(Address(user_id=user_id, email_address=email_address))
    session.commit()
