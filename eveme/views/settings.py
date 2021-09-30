"""
EVEME settings view.

URLs include:
/settings/
/structures/
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

    # Get user's broker fee and transaction tax if exist, otherwise leave field blank
    user_ref = db.reference('users/' + current_user.id)

    if (user_ref.child('brokerFee').get()):
        context['brokerFee'] = user_ref.child('brokerFee').get()

    if (user_ref.child('transactionTax').get()):
        context['transactionTax'] = user_ref.child('transactionTax').get()

    context['structureAccess'] = user_ref.child('structureAccess').get()

    return flask.render_template("settings.html", context=context)


@eveme.app.route('/structures/', methods=['POST', 'DELETE'])
def structure_mod():
    """Handle various additions/deletions from a user's structure list."""
    context = {}
    # 
    if flask.request.method == 'POST':
        print('dog')
        return flask.render_template("structures.html", context=context)
