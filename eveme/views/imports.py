"""
EVEME imports view.

URLs include:
/imports/
"""
from base64 import decodestring
import flask
import eveme
import eveme.helper
import requests
from flask_login import current_user
from firebase_admin import db


@eveme.app.route('/imports/', methods=['GET', 'POST'])
def show_imports():
    """Display /imports/ route."""

    context = {}
    context['isPost'] = False

    if flask.request.method == 'POST':
        # Get item names from IDs
        context['isPost'] = True

        if flask.request.form['source'] == flask.request.form['destination']:
            context['sourceDestoSame'] = True
            return flask.render_template("imports.html", context=context)

        source = flask.request.form['source']
        destination = flask.request.form['destination']

        if flask.request.form['source'] == 'jita':
            source = '60003760'
        elif flask.request.form['destination'] == 'jita':
            destination = '60003760'
        # Update price data for source and destination
        ref = db.reference('prices')

        # TODO: Add check box on form to see if user needs to update price data
        eveme.helper.updatePriceData(destination)

        destoIDsBuy = ref.child(destination).child('buy').get()
        destoIDsSell = ref.child(destination).child('sell').get()

        destoIDs = list(set(destoIDsBuy.keys()) | set(destoIDsSell.keys()))
        chunks = [destoIDs[x:x+200] for x in range(0, len(destoIDs), 200)]
        chunkStrings = []
        for chunk in chunks:
            chunkStrings.append(','.join(chunk))

        destoIDsString = ','.join(destoIDs)
        prices = []
        if source == '60003760':
            region = eveme.helper.getRegionFromStructure(60003760)
            for chunkString in chunkStrings:
                # print(chunkString)
                priceDataRequest = ("https://market.fuzzwork.co.uk/aggregates/?station=60003760&types={}".format(chunkString))
                res = requests.get(priceDataRequest)
                res.raise_for_status()
                print(len(res.json()))
                prices.append(res.json())
        else:
            eveme.helper.updatePriceData(source)
        print(prices[0])
        # Get absolute difference between source and destination prices

        # Get percent difference between source and destination prices

        return flask.render_template("imports.html", context=context)

    context['structures'] = db.reference('users/' + current_user.id + '/structureAccess').get()

    if current_user.is_authenticated:
        eveme.helper.refreshAuth()
    return flask.render_template("imports.html", context=context)
