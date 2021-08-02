"""
EVEME index (main) view.

URLs include:
/
"""
import flask
import eveme
import eveme.helper
from flask_login import current_user


@eveme.app.route('/')
def show_index():
    """Display / route."""
    if current_user.is_authenticated:
        eveme.helper.refreshAuth()
    return flask.render_template("index.html")
