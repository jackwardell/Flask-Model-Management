# import enum
# import pickle
from datetime import date
from datetime import datetime
from datetime import time
from datetime import timedelta
from decimal import Decimal

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import BigInteger
from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import Date
from sqlalchemy import DateTime
from sqlalchemy import Float
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import Interval
from sqlalchemy import LargeBinary
from sqlalchemy import Numeric
from sqlalchemy import SmallInteger
from sqlalchemy import sql
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy import Time
from sqlalchemy import Unicode
from sqlalchemy import UnicodeText
from sqlalchemy.orm import relationship

# from sqlalchemy import Enum
# from sqlalchemy import PickleType

db = SQLAlchemy()

# class RGBColours(enum.Enum):
#     red = 1
#     green = 2
#     blue = 3


USERS = [
    ("hello", "world", True, "hello.world@mail.com"),
    ("goodbye", "world", False, "gb@aol.com"),
    ("another", "person", False, "lol@gg.co"),
]

POSTS = [
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


class Post(db.Model):
    __tablename__ = "post"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    created_at = Column(DateTime, server_default=sql.func.now(), nullable=False)
    post = Column(Text, nullable=False)


class RandomTypeTable(db.Model):
    __tablename__ = "random_type_table"

    id = Column(Integer, primary_key=True, autoincrement=True)
    big_integer = Column(BigInteger)
    boolean = Column(Boolean)
    date = Column(Date)
    datetime = Column(DateTime)
    # enum = Column(Enum(RGBColours))
    float = Column(Float)
    integer = Column(Integer)
    interval = Column(Interval)
    large_binary = Column(LargeBinary)
    numeric = Column(Numeric)
    # pickle_type = Column(PickleType)
    small_integer = Column(SmallInteger)
    string = Column(String)
    text = Column(Text)
    time = Column(Time)
    unicode = Column(Unicode)
    unicode_text = Column(UnicodeText)


random_type_table_mock_data = [
    {
        "big_integer": 123456789123456789,
        "boolean": True,
        "date": date(2020, 11, 20),
        "datetime": datetime(2000, 6, 25, 20, 30, 50, 10),
        # "enum": "red",
        "float": 0.123456789,
        "integer": 420,
        "interval": timedelta(1, 2, 3, 4),
        "large_binary": b"1234567890-=qwertyuiop[]asdfghjkl;'`zxcvbnm,./",
        "numeric": Decimal(13129.6474859),
        # "pickle_type": pickle.dumps(["hello", "world"]),
        "small_integer": 1,
        "string": "hello world",
        "text": "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nullam fermentum nisl at tempus sollicitudin. Praesent vel congue neque. Integer sit amet neque gravida, accumsan nisi nec, dignissim sem. Pellentesque interdum hendrerit arcu id tempor. Fusce maximus turpis ac dui iaculis, eget consequat eros laoreet. Maecenas vestibulum est ac ex viverra, at molestie lorem rhoncus. Ut et erat sem. Mauris porttitor, neque ac pretium tempus, augue mi pretium ex, ac mollis lorem ligula at arcu. Cras efficitur convallis sapien eget accumsan. Etiam lobortis ullamcorper tellus sagittis cursus. Aenean ut nunc ut odio tempor porttitor. Nullam in tincidunt nunc. Quisque euismod vehicula massa, nec finibus tortor dapibus ac. Pellentesque viverra, felis at mattis placerat, mi magna viverra mauris, faucibus gravida purus urna eget urna.",
        "time": time(10, 11, 12, 13),
        "unicode": "goodbye world",
        "unicode_text": "Nunc et eros nulla. Ut tristique at quam faucibus rhoncus. Fusce ut vehicula justo, ac pretium metus. Sed ultrices magna ut rhoncus sollicitudin. Duis ipsum mi, congue eget varius at, blandit sit amet dolor. Vestibulum nec sem eu sem vestibulum luctus non non ante. Praesent sagittis iaculis tellus at ullamcorper.",
    }
]


def populate(session):
    for user_id, (first_name, last_name, is_admin, email_address) in enumerate(USERS):
        session.add(User(first_name=first_name, last_name=last_name, is_admin=is_admin))
        session.add(Address(user_id=user_id, email_address=email_address))
    for row in random_type_table_mock_data:
        session.add(RandomTypeTable(**row))
    session.commit()
