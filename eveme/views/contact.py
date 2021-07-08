"""
EVEME index (contact) view.

URLs include:
/contact/
"""
import flask
import eveme


@eveme.app.route('/contact/')
def show_contact():
    """Display / route."""
    context = {}
    return flask.render_template("contact.html", **context)
