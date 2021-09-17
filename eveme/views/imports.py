"""
EVEME imports view.

URLs include:
/imports/
"""
import flask
import eveme
import eveme.helper
import requests
import os
import pathlib
import json
import time
import datetime
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
        json_url = os.path.join(pathlib.Path().resolve(), "eveme/static/json", "marketGroupTypes.json")
        marketGroupTypes = dict(json.load(open(json_url)))

        # Load selected groups from form
        groups = json.loads(flask.request.form['jsfields'])
        groups = [str(i) for i in groups]
        # Get group types for selected groups
        groupTypes = []
        for group in groups:
            if group in marketGroupTypes.keys():
                groupTypes += marketGroupTypes[group]
            else:
                groupTypes.append(group)
        # TODO: Figure out a way to not have to convert so much
        groupTypes = [str(i) for i in groupTypes]
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

        typeIdsWithData = []

        for typeID in groupTypes:
            # TODO: Fix handling for item not existing in source and/or desto
            context['imports'][typeID] = {}
            if typeID in destoPrices.keys():
                if destoPrices[typeID]['sell']['min'] < 99999999999999999999:
                    context['imports'][typeID]['destoPrice'] = destoPrices[typeID]['sell']['min']
                else:
                    context['imports'][typeID]['destoPrice'] = 1
                context['imports'][typeID]['sourcePrice'] = float(sourcePrices[str(typeID)]['sell']['min'])
                context['imports'][typeID]['numOrders'] = destoPrices[typeID]['sell']['numOrders']
                context['imports'][typeID]['remainingVolume'] = destoPrices[typeID]['sell']['remainingVolume']
                typeIdsWithData.append(typeID)
            else:
                if typeID in sourcePrices.keys():
                    context['imports'][typeID]['sourcePrice'] = float(sourcePrices[str(typeID)]['sell']['min'])
                else:
                    context['imports'][typeID]['sourcePrice'] = 0
                context['imports'][typeID]['destoPrice'] = 1
                context['imports'][typeID]['numOrders'] = 0
                context['imports'][typeID]['remainingVolume'] = 0
                print(invTypes[typeID]['typeName'], ' NOT IN DESTO PRICES')
            context['imports'][typeID]['itemName'] = invTypes[typeID]['typeName']
            context['imports'][typeID]['m3'] = invTypes[typeID]['volume']
        destoRegion = eveme.helper.getRegionFromStructure(destination, headers=headers)

        # TODO: Make this more efficient. Maybe download historical data and save to static file? Cache this
        # TODO: Make so user selects karkinos routes instead of systems.
        # TODO: Make this so it only pulls typeIDs that are present at desto
        datfmt = "%Y-%m-%d"
        analysisSeconds = analysisPeriod * 86400
        for typeID in groupTypes:
            item_time = time.time()
            if typeID in typeIdsWithData:
                dataResponse = requests.get("https://esi.evetech.net/latest/markets/{}/"
                                            "history/?datasource=tranquility&type_id={}".format(int(destoRegion), int(typeID)))
                dataResponse.raise_for_status()
                if dataResponse.status_code != 204:
                    slicedHistData = []
                    historicalData = dataResponse.json()
                    # print("--- API for " + typeID + " in imports took %s seconds ---" % (time.time() - item_time))
                    # Slice historical data to match analysis period
                    for data in historicalData:
                        d = datetime.datetime.strptime(data['date'], datfmt).timestamp()
                        if (d + analysisSeconds > int(time.time())):
                            slicedHistData.append(data)
                    if slicedHistData:
                        totalVol = 0
                        for day in slicedHistData:
                            totalVol += day['volume']
                        totalVol = float(totalVol)
                        dailyVolAverage = totalVol / analysisPeriod
                        if typeID == 40567:
                            print('mantis average:', dailyVolAverage)
                        context['imports'][typeID]['aggPeriodAvg'] = aggregatePeriod * dailyVolAverage
                    else:
                        context['imports'][typeID]['aggPeriodAvg'] = 1
                else:
                    context['imports'][typeID]['aggPeriodAvg'] = 1
            else:
                context['imports'][typeID]['aggPeriodAvg'] = 1
            # print("--- item " + typeID + " in imports took %s seconds ---" % (time.time() - item_time))

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

    json_url = os.path.join(pathlib.Path().resolve(), "eveme/static/json", "marketGroups.json")
    context['marketGroups'] = dict(json.load(open(json_url)))

    context['structures'] = db.reference('users/' + current_user.id + '/structureAccess').get()

    if current_user.is_authenticated:
        eveme.helper.refreshAuth()
    print("--- show_imports() showing form took %s seconds ---" % (time.time() - start_time))
    return flask.render_template("imports.html", context=context)
