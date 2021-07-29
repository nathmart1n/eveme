"""
EVEME settings view.

URLs include:
/settings/
"""
import flask
import eveme


@eveme.app.route('/settings/', methods=['GET', 'POST'])
def show_settings():
    """Display /settings/ route and pull any scopes that need to be refreshed."""
    context = {}

    if flask.request.method == 'POST':
        return flask.render_template("settings.html", **context)

    return flask.render_template("settings.html")
