"""
EVEME settings view.

URLs include:
/settings/
"""
import flask
import eveme
import eveme.helper


@eveme.app.route('/settings/', methods=['GET', 'POST'])
def show_settings():
    """Display /settings/ route and pull any scopes that need to be refreshed."""
    context = {}

    eveme.helper.refreshAuth()

    if flask.request.method == 'POST':
        if 'userOrders' in flask.request.form:
            print('a')
        elif 'userData' in flask.request.form:
            eveme.helper.updateUserData()
        elif 'priceData' in flask.request.form:
            eveme.helper.updatePriceData()
        return flask.render_template("settings.html")

    return flask.render_template("settings.html")
