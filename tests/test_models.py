# from tests.conftest import User
# from flask_model_management import Model
#
#
# def make_user():
#     user = User(first_name="hello", last_name="world")
#     return user
#
#
# def test_user_model(session):
#     session.add(make_user())
#     session.commit()
#     assert session.query(User).count() == 1
#
#
# def test_model(session, app):
#     session.add(make_user())
#     session.commit()
#
#     user = session.query(User).first()
#     model = Model(user)
#     assert False
