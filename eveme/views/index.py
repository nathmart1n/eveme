"""
EVEME index (main) view.

URLs include:
/
"""
import flask
import eveme


@eveme.app.route('/')
def show_index():
    """Display / route."""
    return flask.render_template("index.html")
