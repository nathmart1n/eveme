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


def insertStructure(user_id, structure_id):
    ref = db.reference('users/' + user_id + '/structureAccess')
    ref.put(structure_id)


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
        transaction['item_name'] = invTypes[str(transaction['type_id'])]

    if User.get(str(charID)):
        charRef = ref.child(str(charID))
        charRef.update(new)
    else:
        ref.set({
            str(charID): new
        })

    print("--- updateUserData() with took %s seconds ---" % (time.time() - start_time))
    return None


def updateUserOrders():
    """Queries ESI and updates user's market orders in DB."""
    return None


def updatePriceData():
    """Queries ESI data for structures user has orders in and updates max/min prices."""
    start_time = time.time()
    ref = db.reference('prices')
    headers = createHeaders(current_user.accessToken)
    for structureID in current_user.structureAccess:
        if structureID < 100000000:
            # TODO: Fill this out for region orders then narrow down to station.
            return None
        else:
            structureOrdersQuery = ("https://esi.evetech.net/latest/markets/structures"
                                    "/{}/".format(structureID))
            res = requests.get(structureOrdersQuery, headers=headers)
            res.raise_for_status()
            numPages = res.headers['X-Pages']
            structureOrders = res.json()

        for i in range(1, int(numPages)):
            structureOrdersQuery = ("https://esi.evetech.net/latest/markets/structures"
                                    "/{}/?datasource=tranquility&page="
                                    "{}".format(structureID, i + 1))
            res = requests.get(structureOrdersQuery, headers=headers)
            res.raise_for_status()
            numPages = res.headers['X-Pages']
            structureOrders.extend(res.json())

    prices = {
        "sell": {},
        "buy": {}
    }

    for order in structureOrders:
        if order['is_buy_order']:
            if order['type_id'] in prices['buy'].keys():
                if order['price'] > prices['buy'][order['type_id']]:
                    prices['buy'][order['type_id']] = order['price']
            else:
                prices['buy'][order['type_id']] = order['price']
        else:
            if order['type_id'] in prices['sell'].keys():
                if order['price'] < prices['sell'][order['type_id']]:
                    prices['sell'][order['type_id']] = order['price']
            else:
                prices['sell'][order['type_id']] = order['price']
    # print(prices)
    ref.set(prices)
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
