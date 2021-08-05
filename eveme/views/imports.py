"""
EVEME imports view.

URLs include:
/imports/
"""
import flask
import eveme
import eveme.helper
from flask_login import current_user


@eveme.app.route('/imports/', methods=['GET', 'POST'])
def show_imports():
    """Display /imports/ route."""
    context = {}

    if flask.request.method == 'POST':
        
        return flask.render_template("imports.html", **context)

    if current_user.is_authenticated:
        eveme.helper.refreshAuth()
    return flask.render_template("imports.html", **context)
