"""EVEME package initializer."""
import os
from flask import Flask
from flask_login import LoginManager
from eveme.user import User
# app is a single object used by all the code modules in this package
app = Flask(__name__, instance_relative_config=True)

login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)


@app.template_filter()
def numberFormat(value):
    value = float(value)
    return "{:,.2f}".format(value)


app.config.from_mapping(
    SECRET_KEY='dev',
    DATABASE=os.path.join(app.instance_path, 'flaskr.sqlite'),
)

app.config.from_pyfile('config.py', silent=True)

# Tell our app about views and model.  This is dangerously close to a
# circular import, which is naughty, but Flask was designed that way.
# (Reference http://flask.pocoo.org/docs/patterns/packages/)  We're
# going to tell pylint and pycodestyle to ignore this coding style violation.
import eveme.views  # noqa: E402  pylint: disable=wrong-import-position
import eveme.model  # noqa: E402  pylint: disable=wrong-import-position
