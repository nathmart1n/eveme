"""
EVEME index (about) view.

URLs include:
/about/
"""
import flask
import eveme


@eveme.app.route('/about/')
def show_about():
    """Display / route."""
    context = {}
    return flask.render_template("about.html", **context)
