"""
EVEME index (main) view.

URLs include:
/
"""
import flask
import eveme
import eveme.helper


@eveme.app.route('/')
def show_index():
    """Display / route."""
    eveme.helper.refreshAuth()
    return flask.render_template("index.html")
