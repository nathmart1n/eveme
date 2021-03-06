"""
EVEME contact view.

URLs include:
/contact/
"""
import flask
import eveme
import eveme.helper
from flask_login import current_user


@eveme.app.route('/contact/')
def show_contact():
    """Display /contact/ route."""
    context = {}
    if current_user.is_authenticated:
        eveme.helper.refreshAuth()
    return flask.render_template("contact.html", **context)
