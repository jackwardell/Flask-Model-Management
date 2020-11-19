# Flask-Model-Management
A Flask extension for managing Flask-SQLAlchemy models

# Status: In Alpha Development
BE WARNED: INSTALLING CRUD APPLICATIONS INTO PRODUCTION SERVERS ALLOWS USERS TO PERFORM POTENTIALLY IRREVERSIBLE DATA OPERATIONS

# Install
* pip install:
```
pip install flask_model_management
```

# Use
* an example of how to use without app factory might look something like:
```
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_model_management import ModelManager

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'
db = SQLAlchemy(app)
model_manager = ModelManager(app, db)

# showing model declaration for the example
class User(db.Model):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    username = Column(String)

model_manager.register_model(User)
```


* with app factory:
```
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_model_management import ModelManager

db = SQLAlchemy()

# showing model declaration for the example
class User(db.Model):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    username = Column(String, nullable=False)

model_manager = ModelManager()

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'
    db.init_app(app)
    model_manager.init_app(app, db)

    model_manager.register_model(User, nullable=False)
```
