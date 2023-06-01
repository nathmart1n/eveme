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
            # TODO: Can we cut down on this code duplication?
            if source == '60003760':
                eveme.helper.updatePriceData(destination)
                destoPrices = prices_ref.child(destination).get()

                destoIDs = list(destoPrices.keys())

                chunks = [destoIDs[x:x + 200] for x in range(0, len(destoIDs), 200)]
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
            elif destination == '60003760':
                eveme.helper.updatePriceData(source)
                sourcePrices = prices_ref.child(source).get()

                sourceIDs = list(sourcePrices.keys())

                chunks = [sourceIDs[x:x + 200] for x in range(0, len(sourceIDs), 200)]
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

        destoPrices = prices_ref.child(destination).get()
        sourcePrices = prices_ref.child(source).get()

        typeIdsWithData = []

        for typeID in groupTypes:
            # The only issue with this is if the item does not currently exist in either the source or the desto, it will not pull any info.
            # This is sorta expected behavior, but if the item just sold out of everything
            # the user will miss out on a potential opportunity.
            # Generally though, the purpose of this app isn't to capitalize on short-term inventory shortages,
            # but rather long-term price advantages.
            # Basically, not necessary to fix.
            if typeID in destoPrices.keys() and typeID in sourcePrices.keys() and float(destoPrices[typeID]['sell']['orderCount']) > 0:
                context['imports'][typeID] = {}
                context['imports'][typeID]['destoPrice'] = float(destoPrices[typeID]['sell']['min'])
                context['imports'][typeID]['sourcePrice'] = float(sourcePrices[typeID]['sell']['min'])
                context['imports'][typeID]['orderCount'] = float(destoPrices[typeID]['sell']['orderCount'])
                context['imports'][typeID]['volume'] = float(destoPrices[typeID]['sell']['volume'])
                typeIdsWithData.append(typeID)
                context['imports'][typeID]['itemName'] = invTypes[typeID]['typeName']
                context['imports'][typeID]['m3'] = invTypes[typeID]['volume']
        # Need this because region checking for Jita vs player structures is different.
        # Need a way to differentiate between stations and player structures
        # Because this will happen for places like Hek, Amarr, etc.
        if destination == '60003760':
            destoRegion = eveme.helper.getRegionFromStructure(destination)
        else:
            destoRegion = eveme.helper.getRegionFromStructure(destination, headers=headers)

        # TODO: Download historical data once a day. Store in database? Similar to eyeonwater/edna data.
        # Look at bottom of updateStaticFiles.py file.
        # TODO: Make so user selects karkinos routes instead of systems.
        datfmt = "%Y-%m-%d"
        analysisSeconds = analysisPeriod * 86400
        for typeID in typeIdsWithData:
            item_time = time.time()
            dataResponse = requests.get("https://esi.evetech.net/latest/markets/{}/"
                                        "history/?datasource=tranquility&type_id={}".format(int(destoRegion), int(typeID)))
            dataResponse.raise_for_status()
            # 204 is the code we want not 200 for whatever reason
            # TODO: Find why 204 and not 200 for comment
            if dataResponse.status_code != 204:
                slicedHistData = []
                historicalData = dataResponse.json()
                print("--- API for " + typeID + " in imports took %s seconds ---" % (time.time() - item_time))
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
            # print("--- item " + typeID + " in imports took %s seconds ---" % (time.time() - item_time))

        # Get user defined brokers fee, transaction tax, m3 price for shipping and collat percent for shipping
        user_ref = db.reference('users').child(str(current_user.id))
        context['pricePerM3'] = user_ref.child('iskm3').get()
        context['collateralPercentage'] = user_ref.child('collateralPercent').get() / 100
        context['brokerFee'] = user_ref.child('brokerFee').get() / 100
        context['transactionTax'] = user_ref.child('transactionTax').get() / 100
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
