# Flask-Model-Management
A Flask extension for managing Flask-SQLAlchemy models

# Status: In Alpha Development
BE WARNED: INSTALLING CRUD APPLICATIONS INTO PRODUCTION SERVERS ALLOWS USERS TO PERFORM POTENTIALLY IRREVERSIBLE DATA OPERATIONS

# Install and run example locally
* Clone:
```
git clone https://github.com/jackwardell/Flask-Model-Management.git
```
* Move into directory:
```
cd Flask-Model-Management
```
* Setup locally:
```
&& pip3 install -e .
```
* Run Flask:
```
FLASK_ENV=development FLASK_APP=app flask run
```
* Alter app factory in `app.py` and models in `tests/models.py`
