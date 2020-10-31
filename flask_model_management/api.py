
# class API:
#     def __init__(self, model, session):
#         self.model = model
#         self.session = session
#
#     def get(self):
#         query = self.session.query(self.model)
#         for k, v in request.args.items():
#             query = query.filter_by(**{k: v})
#         return query.all()
#
#     def post(self):
#         model = self.model(**dict(request.args.items()))
#         self.session.add(model)
#         self.session.commit()
#         return model
#
#     def put(self):
#         pass
#
#     def delete(self):
#         pass


# class CRUD:
#     def __init__(self, model, session):
#         self.model = model
#         self.session = session
#
#     def create(self, **kwargs):
#         model = self.model(**kwargs)
#         self.session.add(model)
#         self.session.commit()
#         return model
#
#     def read(self, **kwargs):
#         query = self.session.query(self.model)
#         for k, v in kwargs.items():
#             query = query.filter(**{k: v})
#         return query
#
#     def update(self, **kwargs):
#         query = self.session.query(self.model)
#         for k, v in kwargs.items():
#             query = query.filter(**{k: v})
#         return query
#
#     def delete(self, **kwargs):
#         return self.read(**kwargs).delete()

