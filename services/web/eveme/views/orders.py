"""
EVEME market orders view.

URLs include:
/orders/
"""
import flask
import eveme
import time
import eveme.helper
from flask_login import current_user
from firebase_admin import db


@eveme.app.route('/orders/')
def show_orders():
    """Display /orders/ route."""
    start_time = time.time()
    output = {}
    output['buyOrders'] = []
    output['sellOrders'] = []

    ref = db.reference('users')
    user_ref = ref.child(current_user.id).get()

    if current_user.is_authenticated:
        eveme.helper.refreshAuth()

    if 'buyOrders' in user_ref.keys():
        for id in user_ref['buyOrders'].keys():
            output['buyOrders'].append(user_ref['buyOrders'][id])
        output['buyOrders'] = sorted(output['buyOrders'], key=lambda k: k['itemName'])

    if 'sellOrders' in user_ref.keys():
        for id in user_ref['sellOrders'].keys():
            output['sellOrders'].append(user_ref['sellOrders'][id])
        output['sellOrders'] = sorted(output['sellOrders'], key=lambda k: k['itemName'])

    print("--- show_orders() with took %s seconds ---" % (time.time() - start_time))
    return flask.render_template("orders.html", context=output)
