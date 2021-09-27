import eveme
import requests
import time
import base64
import os
import json
import pathlib
from firebase_admin import db
from flask_login import current_user
from flask import current_app
from eveme.user import User


def createHeaders(access_token):
    return {
            "Authorization": "Bearer {}".format(access_token)
           }


def getStructures(user_id):
    start_time = time.time()
    ref = db.reference('users/' + user_id)
    output = []
    structs = ref.get()['structureAccess']
    for structure in structs:
        output.append(structure)
    print("--- getStructures() took %s seconds ---" % (time.time() - start_time))
    return output


def esiRequest(requestType, variable, charHeaders=None):
    """Performs request to ESI API. userToken necessary if request type requires auth."""
    start_time = time.time()
    requestURL = {
        'charInfo': "https://esi.evetech.net/latest/characters/{}/".format(variable),
        'charOrders': "https://esi.evetech.net/latest/characters/{}/orders/".format(variable),
        'corpInfo': "https://esi.evetech.net/latest/corporations/{}/".format(variable),
        'allianceInfo': "https://esi.evetech.net/latest/alliances/{}/".format(variable),
        'structureInfo': "https://esi.evetech.net/latest/universe/structures/{}/".format(variable),
        'walletBalance': "https://esi.evetech.net/latest/characters/{}/wallet".format(variable),
        'portrait': "https://esi.evetech.net/latest/characters/{}/portrait/".format(variable),
        'walletTransactions': "https://esi.evetech.net/latest/characters/{}/wallet/transactions".format(variable),
        'stationInfo': "https://esi.evetech.net/latest/universe/stations/{}/".format(variable),
        'systemInfo': "https://esi.evetech.net/latest/universe/systems/{}/".format(variable),
        'constellationInfo': "https://esi.evetech.net/latest/universe/constellations/{}/".format(variable),
    }

    if charHeaders:
        res = requests.get(requestURL[requestType], headers=charHeaders)
    else:
        res = requests.get(requestURL[requestType])

    print("--- esiRequest() with " + requestType + " took %s seconds ---" % (time.time() - start_time))
    return res.json()


def updateUserData():
    """Queries ESI and updates user's character sheet in DB."""
    start_time = time.time()
    json_url = os.path.join(pathlib.Path().resolve(), "eveme/static/json", "invTypes.json")
    invTypes = dict(json.load(open(json_url)))

    headers = createHeaders(current_user.accessToken)

    # Get current user id
    charID = current_user.id
    # Dict for new info
    new = {}
    # Get public data
    publicData = eveme.helper.esiRequest('charInfo', charID)

    # Get portrait
    portrait = eveme.helper.esiRequest('portrait', charID)

    # Get the user's corporation and alliance
    corporation = eveme.helper.esiRequest('corpInfo', publicData['corporation_id'])

    if 'alliance_id' in publicData.keys():
        alliance = eveme.helper.esiRequest('allianceInfo', publicData['alliance_id'])
        inAlliance = True
        new['alliance'] = alliance['name']

    # Adding our new info
    new['corporation'] = corporation['name']
    new['name'] = publicData['name']
    new['profilePic'] = portrait['px256x256']
    ref = db.reference('users')

    # Get user wallet balance
    balance = eveme.helper.esiRequest('walletBalance', charID, headers)
    new['walletBalance'] = balance
    new['walletTransactions'] = \
        eveme.helper.esiRequest('walletTransactions', charID, headers)
    for transaction in new['walletTransactions']:
        transaction['item_name'] = invTypes[str(transaction['type_id'])]['typeName']

    if User.get(str(charID)):
        charRef = ref.child(str(charID))
        charRef.update(new)
    else:
        ref.set({
            str(charID): new
        })

    print("--- updateUserData() with took %s seconds ---" % (time.time() - start_time))
    return None


def modifyOrder(order, user_info, ref, isBuy, invTypes, structuresChecked):
    """Modify orders to separate into buy sell and substitute in highest/lowest prices."""
    # Rename CCP snake case to our camel case
    order['volumeRemain'] = order.pop('volume_remain')
    order['volumeTotal'] = order.pop('volume_total')
    # Get the itemName from our invTypes typeID to name file
    order['itemName'] = invTypes[str(order['type_id'])]['typeName']
    # StructuresChecked is a list of structure names by location_id, get name from there
    order['structureName'] = structuresChecked[order['location_id']]
    # Add to buy or sell orders depending on order type
    if isBuy:
        order['structureHighest'] = ref.child(str(order['location_id'])).child(str(order['type_id'])).child('buy').child('max').get()
        user_info['buyOrders'][order['order_id']] = order
    else:
        order['structureLowest'] = ref.child(str(order['location_id'])).child(str(order['type_id'])).child('sell').child('min').get()
        user_info['sellOrders'][order['order_id']] = order


def updateUserOrders():
    """Queries ESI and updates user's market orders in DB."""
    start_time = time.time()
    # Load in typeID conversion (invTypes) MAKE THIS ANOTHER FUNCTION
    json_url = os.path.join(pathlib.Path().resolve(), "eveme/static/json", "invTypes.json")
    invTypes = dict(json.load(open(json_url)))

    # Link to structure prices in DB
    ref = db.reference('prices')

    headers = createHeaders(current_user.accessToken)

    orders = eveme.helper.esiRequest('charOrders', current_user.id, headers)

    structuresChecked = {}
    # Set empty info struct
    user_info = {
        'buyOrders': {},
        'sellOrders': {},
        'structureAccess': [],
    }

    if orders:
        for order in orders:
            # eveme.helper.insertStructure(char_id, order['location_id'])
            # Format price with commas

            if order['location_id'] not in structuresChecked.keys():
                structuresChecked[order['location_id']] = eveme.helper.esiRequest('structureInfo', order['location_id'], headers)['name']

            # check each order with order in structure and compare

            if 'is_buy_order' in order.keys():
                modifyOrder(order, user_info, ref, True, invTypes, structuresChecked)
            else:
                modifyOrder(order, user_info, ref, False, invTypes, structuresChecked)

        validStructs = {}

        for structureID in structuresChecked.keys():
            structureOrdersQuery = ("https://esi.evetech.net/latest/markets/structures"
                                    "/{}/".format(structureID))
            res = requests.get(structureOrdersQuery, headers=headers)
            if res.status_code == 200:
                validStructs[structureID] = structuresChecked[structureID]
        user_info['structureAccess'] = validStructs
    else:
        # If there are no orders pop these fields so we dont have errors with Jinja
        user_info.pop('buyOrders')
        user_info.pop('sellOrders')
        user_info.pop('structureAccess')

    User.update(user_info, current_user.id)
    print("--- updateUserOrders() took %s seconds ---" % (time.time() - start_time))
    return None


def getRegionFromStructure(structureID, headers=None):
    if headers:
        structureInfo = esiRequest('structureInfo', structureID, headers)
        systemInfo = esiRequest('systemInfo', structureInfo['solar_system_id'])
    else:
        stationInfo = esiRequest('stationInfo', structureID)
        systemInfo = esiRequest('systemInfo', stationInfo['system_id'])
    constellationInfo = esiRequest('constellationInfo', systemInfo['constellation_id'])
    return constellationInfo['region_id']


def updatePriceData(structureID=None):
    """Queries ESI data for structures user has orders in and updates max/min prices."""
    start_time = time.time()
    ref = db.reference('prices')
    # Check if structureID passed in, if not we need to pull all from DB
    if structureID:
        structures = [structureID]
    else:
        structures = db.reference('users/'+current_user.id+'/structureAccess').get()
    # Generate headers
    headers = createHeaders(current_user.accessToken)
    for selectedID in structures:
        # If structure is less than 100000000 its a station, greater its a player structure
        if int(selectedID) < 100000000:
            region = getRegionFromStructure(selectedID)
            regionOrdersQuery = ("https://esi.evetech.net/latest/markets/{}/orders".format(region))
            res = requests.get(regionOrdersQuery)
            res.raise_for_status()
            numPages = res.headers['X-Pages']
            regionOrders = res.json()

            for i in range(1, int(numPages)):
                regionOrdersQuery = ("https://esi.evetech.net/latest/markets/{}/orders?datasource=tranquility&page="
                                     "{}".format(region, i + 1))
                res = requests.get(regionOrdersQuery)
                res.raise_for_status()
                numPages = res.headers['X-Pages']
                regionOrders.extend(res.json())

            structureOrders = []

            for order in regionOrders:
                if order['location_id'] == selectedID:
                    structureOrders.append(order)
        else:
            structureOrdersQuery = ("https://esi.evetech.net/latest/markets/structures"
                                    "/{}/".format(selectedID))
            res = requests.get(structureOrdersQuery, headers=headers)
            res.raise_for_status()
            numPages = res.headers['X-Pages']
            structureOrders = res.json()

            for i in range(1, int(numPages)):
                structureOrdersQuery = ("https://esi.evetech.net/latest/markets/structures"
                                        "/{}/?datasource=tranquility&page="
                                        "{}".format(selectedID, i + 1))
                res = requests.get(structureOrdersQuery, headers=headers)
                res.raise_for_status()
                numPages = res.headers['X-Pages']
                structureOrders.extend(res.json())

        prices = {}
        # Update price format to match that of fuzzwork jita prices
        for order in structureOrders:
            if order['type_id'] in prices.keys():
                if order['is_buy_order']:
                    prices[order['type_id']]['buy']['numOrders'] += 1
                    prices[order['type_id']]['buy']['remainingVolume'] += order['volume_remain']
                    if order['price'] > prices[order['type_id']]['buy']['max']:
                        prices[order['type_id']]['buy']['max'] = order['price']
                else:
                    prices[order['type_id']]['sell']['numOrders'] += 1
                    prices[order['type_id']]['sell']['remainingVolume'] += order['volume_remain']
                    if order['price'] < prices[order['type_id']]['sell']['min']:
                        prices[order['type_id']]['sell']['min'] = order['price']
            else:
                prices[order['type_id']] = {
                    "buy": {
                        "max": -1,
                        "numOrders": 0,
                        "remainingVolume": 0
                    },
                    "sell": {
                        "min": 99999999999999999999,
                        "numOrders": 0,
                        "remainingVolume": 0
                    }
                }
                if order['is_buy_order']:
                    prices[order['type_id']]['buy']['max'] = order['price']
                    prices[order['type_id']]['buy']['numOrders'] += 1
                    prices[order['type_id']]['buy']['remainingVolume'] += order['volume_remain']
                else:
                    prices[order['type_id']]['sell']['min'] = order['price']
                    prices[order['type_id']]['sell']['numOrders'] += 1
                    prices[order['type_id']]['sell']['remainingVolume'] += order['volume_remain']
        # print(selectedID)
        ref.child(selectedID).set(prices)
    print("--- updatePriceData() with took %s seconds ---" % (time.time() - start_time))
    return None


def refreshAuth():
    """Refreshes auth token if time greater than 20 mins."""
    start_time = time.time()
    if time.time() - current_user.authTime >= 1200:
        newAuthTime = time.time()
        user_pass = "{}:{}".format(current_app.config['ESI_CLIENT_ID'],
                                   current_app.config['ESI_SECRET_KEY'])
        basic_auth = base64.urlsafe_b64encode(user_pass.encode('utf-8')).decode()
        auth_header = "Basic {}".format(basic_auth)
        form_values = {
            "grant_type": "refresh_token",
            "refresh_token": current_user.refreshToken,
        }

        headers = {"Authorization": auth_header}
        res = send_token_request(form_values, add_headers=headers)
        # TODO: Implement handling other than 200 codes
        if res.status_code == 200:
            data = res.json()
            current_user.accessToken = data["access_token"]
            User.updateAuthToken(data['access_token'], time.time(), current_user.id)
        else:
            print('--------WEE WOOO SHIT BROKE WEE WOO REFRESH AUTH BROKE WEE WOO--------')
    print("--- refreshAuth() with took %s seconds ---" % (time.time() - start_time))
    return None


def send_token_request(form_values, add_headers={}):
    """Sends a request for an authorization token to the EVE SSO.

    Args:
        form_values: A dict containing the form encoded values that should be
                     sent with the request
        add_headers: A dict containing additional headers to send
    Returns:
        requests.Response: A requests Response object
    """
    start_time = time.time()
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Host": "login.eveonline.com",
    }

    if add_headers:
        headers.update(add_headers)

    res = requests.post(
        "https://login.eveonline.com/v2/oauth/token",
        data=form_values,
        headers=headers,
    )

    res.raise_for_status()
    print("--- send_token_request() with took %s seconds ---" % (time.time() - start_time))
    return res


def structNameFromID(structID):
    """Gets structure name given ID.

    Args:
        structID: A given structure ID
    Returns:
        structName: A string containing the structure name, returns NONE if doesn't exist
    """
    start_time = time.time()

    res = requests.get("https://esi.evetech.net/latest/universe/structures/{}/".format(structID))

    if res.status_code == 200:
        return res.json()['name']
    else:
        return None
