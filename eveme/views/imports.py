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

        headers = eveme.helper.createHeaders(current_user.accessToken)

        if flask.request.form['source'] == flask.request.form['destination']:
            context['sourceDestoSame'] = True
            return flask.render_template("imports.html", context=context)

        # Analysis period represents the number of days back we should use to compute average volume for the given aggregate period
        analysisPeriod = int(flask.request.form['analysisPeriod'])
        aggregatePeriod = int(flask.request.form['aggregatePeriod'])

        source = flask.request.form['source']
        destination = flask.request.form['destination']

        if flask.request.form['source'] == 'jita':
            source = '60003760'
        elif flask.request.form['destination'] == 'jita':
            destination = '60003760'
        # Update price data for source and destination
        prices_ref = db.reference('prices')

        # TODO: Add check box for using buy or sell orders in source/desto, for now default to sell in both

        if 'updatePrices' in flask.request.form.keys():
            eveme.helper.updatePriceData(destination)

            if source == '60003760':
                destoPrices = prices_ref.child(destination).get()

                destoIDs = list(destoPrices.keys())

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
                prices_ref.child('60003760').update(prices)
            else:
                eveme.helper.updatePriceData(source)

        destoPrices = prices_ref.child(destination).get()
        sourcePrices = prices_ref.child(source).get()

        for typeID in destoPrices.keys():
            # TODO: Make this togglable with something in the form.
            if destoPrices[typeID]['sell']['min'] < 99999999999999999999:
                if destoPrices[typeID]['sell']['min'] - float(sourcePrices[str(typeID)]['sell']['min']) > 0 and invTypes[typeID]['volume'] < 350000:
                    context['imports'][typeID] = {}
                    context['imports'][typeID]['sourcePrice'] = float(sourcePrices[str(typeID)]['sell']['min'])
                    context['imports'][typeID]['destoPrice'] = destoPrices[typeID]['sell']['min']
                    context['imports'][typeID]['itemName'] = invTypes[typeID]['typeName']
                    context['imports'][typeID]['m3'] = invTypes[typeID]['volume']
                    context['imports'][typeID]['numOrders'] = destoPrices[typeID]['sell']['numOrders']
                    context['imports'][typeID]['remainingVolume'] = destoPrices[typeID]['sell']['remainingVolume']
        destoRegion = eveme.helper.getRegionFromStructure(destination, headers=headers)
        print(len(context['imports'].keys()))

        # TODO: Make this more efficient. Maybe download historical data and save to static file?
        # Let user select what market groups they want.
        # That then queries our historical data static file instead of querying API

        # TODO: Make so user selects karkinos routes instead of systems.
        for typeID in context['imports'].keys():
            item_time = time.time()
            historicalData = requests.get("https://esi.evetech.net/latest/markets/{}/"
                                          "history/?datasource=tranquility&type_id={}".format(int(destoRegion), int(typeID))).json()
            # print("--- API for " + typeID + " in imports took %s seconds ---" % (time.time() - item_time))
            # Slice historical data to match analysis period
            slicedHistData = historicalData[-analysisPeriod:]
            totalVol = 0
            if slicedHistData:
                for day in slicedHistData:
                    totalVol += day['volume']
                totalVol = float(totalVol)
                dailyVolAverage = totalVol / len(slicedHistData)
                context['imports'][typeID]['aggPeriodAvg'] = aggregatePeriod * dailyVolAverage
                print("--- item " + typeID + " in imports took %s seconds ---" % (time.time() - item_time))

        # TODO: Make this variable dependent on user input
        context['pricePerM3'] = 820
        context['collateralPercentage'] = 0.015

        # Get user defined brokers fee and transaction tax
        user_ref = db.reference('users').child(str(current_user.id))
        context['brokerFee'] = user_ref.child('brokerFee').get()
        context['transactionTax'] = user_ref.child('transactionTax').get()

        # TODO: Get absolute difference between source and destination prices
        # TODO: Get percent difference between source and destination prices
        print("--- show_imports() showing trades took %s seconds ---" % (time.time() - start_time))
        return flask.render_template("imports.html", context=context)

    context['structures'] = db.reference('users/' + current_user.id + '/structureAccess').get()

    if current_user.is_authenticated:
        eveme.helper.refreshAuth()
    print("--- show_imports() showing form took %s seconds ---" % (time.time() - start_time))
    return flask.render_template("imports.html", context=context)
