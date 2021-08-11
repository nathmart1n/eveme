"""
EVEME settings view.

URLs include:
/settings/
"""
import flask
import eveme
import eveme.helper
from flask_login import current_user
from firebase_admin import db


@eveme.app.route('/settings/', methods=['GET', 'POST'])
def show_settings():
    """Display /settings/ route and pull any scopes that need to be refreshed."""
    context = {}

    eveme.helper.refreshAuth()

    if flask.request.method == 'POST':
        ref = db.reference('users').child(str(current_user.id))

        if 'priceData' in flask.request.form:
            eveme.helper.updatePriceData()
        if 'userOrders' in flask.request.form:
            eveme.helper.updateUserOrders()
        if 'userData' in flask.request.form:
            eveme.helper.updateUserData()
        if flask.request.form['brokerFee'] != '':
            print(flask.request.form['brokerFee'])
            ref.update({
                'brokerFee': float(flask.request.form['brokerFee'])
            })
        if flask.request.form['transactionTax'] != '':
            ref.update({
                'transactionTax': float(flask.request.form['transactionTax'])
            })
        return flask.render_template("settings.html")

    return flask.render_template("settings.html")
