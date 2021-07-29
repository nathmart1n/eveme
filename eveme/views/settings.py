"""
EVEME settings view.

URLs include:
/settings/
"""
import flask
import eveme


@eveme.app.route('/settings/')
def show_settings():
    """Display / route."""
    context = {}
    return flask.render_template("settings.html", **context)
