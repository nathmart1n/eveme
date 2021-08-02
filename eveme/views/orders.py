"""
EVEME index (about) view.

URLs include:
/about/
"""
import flask
import eveme
import eveme.helper
from flask_login import current_user


@eveme.app.route('/orders/')
def show_orders():
    """Display /orders/ route."""
    context = {}
    if current_user.is_authenticated:
        eveme.helper.refreshAuth()
    return flask.render_template("orders.html", **context)
