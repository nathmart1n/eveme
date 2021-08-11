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
import os
import pathlib
import json
import time
from flask_login import current_user
from firebase_admin import db


@eveme.app.route('/imports/', methods=['GET', 'POST'])
def show_imports():
    """Display /imports/ route."""
    start_time = time.time()
    context = {}
    context['isPost'] = False

    if flask.request.method == 'POST':
        # Import item ids to names file
        json_url = os.path.join(pathlib.Path().resolve(), "eveme/static/json", "invTypes.json")
        invTypes = dict(json.load(open(json_url)))
        # Get item names from IDs
        context['isPost'] = True
        context['imports'] = {}

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

        # TODO: Add check box for using buy or sell orders in source/desto, for now default to sell in both

        if 'updatePrices' in flask.request.form.keys():
            eveme.helper.updatePriceData(destination)

        destoPrices = ref.child(destination).child('sell').get()

        destoIDs = list(destoPrices.keys())
        sourcePrices = {}
        if source == '60003760':
            chunks = [destoIDs[x:x+200] for x in range(0, len(destoIDs), 200)]
            chunkStrings = []
            for chunk in chunks:
                chunkStrings.append(','.join(chunk))
            prices = {}
            for chunkString in chunkStrings:
                priceDataRequest = ("https://market.fuzzwork.co.uk/aggregates/?station=60003760&types={}".format(chunkString))
                res = requests.get(priceDataRequest)
                res.raise_for_status()
                prices.update(res.json())
            sourcePrices = prices
        else:
            eveme.helper.updatePriceData(source)
        for typeID in destoIDs:
            context['imports'][typeID] = {}
            context['imports'][typeID]['sourcePrice'] = float(sourcePrices[str(typeID)]['sell']['min'])
            context['imports'][typeID]['destoPrice'] = destoPrices[typeID]
            context['imports'][typeID]['itemName'] = invTypes[typeID]

        # Get absolute difference between source and destination prices
        # Get percent difference between source and destination prices
        print("--- show_imports() showing trades took %s seconds ---" % (time.time() - start_time))
        return flask.render_template("imports.html", context=context)

    context['structures'] = db.reference('users/' + current_user.id + '/structureAccess').get()

    if current_user.is_authenticated:
        eveme.helper.refreshAuth()
    print("--- show_imports() showing form took %s seconds ---" % (time.time() - start_time))
    return flask.render_template("imports.html", context=context)
