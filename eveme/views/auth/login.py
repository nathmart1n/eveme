"""
EVEME index (login) view.

URLs include:
/login/
/success/<char_id>
/callback/
"""
from flask import (
    Flask,
    config,
    current_app,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import login_user, current_user
from eveme.shared_flow import send_token_request, handle_sso_token_response
from eveme.user import User
import eveme.helper
import eveme
import requests
import base64
import json
import os
import pathlib


@eveme.app.route("/login/")
def login():
    """First step in ESI OAuth."""
    request_uri = 'https://login.eveonline.com/v2/oauth/authorize/?response' +\
                  '_type=code&redirect_uri=http%3A%2F%2Flocalhost%3A5000%2F' +\
                  'callback%2F&client_id=' +\
                  current_app.config['ESI_CLIENT_ID'] +\
                  '&scope=esi-markets.read_character_orders.v1+' +\
                  'esi-markets.structure_markets.v1+' +\
                  'esi-universe.read_structures.v1+' +\
                  'esi-assets.read_assets.v1+' +\
                  'esi-wallet.read_character_wallet.v1' +\
                  '&state=ohd9912dn102dn012'
    return redirect(request_uri)


@eveme.app.route("/character/<char_id>")
def character(char_id):
    json_url = os.path.join(pathlib.Path().resolve(), "eveme/static/json", "invTypes.json")
    invTypes = dict(json.load(open(json_url)))

    output = {}
    inAlliance = False

    public = eveme.helper.esiRequest('charInfo', char_id)
    corporation = eveme.helper.esiRequest('corpInfo', public['corporation_id'])

    if 'alliance_id' in public.keys():
        alliance = eveme.helper.esiRequest('allianceInfo', public['alliance_id'])
        inAlliance = True
        output['alliance_name'] = alliance['name']

    output['corp_name'] = corporation['name']
    output['isLoggedInUser'] = False

    if current_user.is_authenticated and char_id == current_user.id:
        output['isLoggedInUser'] = True
        headers = eveme.helper.createHeaders(current_user.accessToken)
        output['name'] = current_user.name
        output['profilePic'] = current_user.profilePic
        output['buyOrders'] = []
        output['sellOrders'] = []

        if current_user.buyOrders != 'None':
            for id in current_user.buyOrders.keys():
                output['buyOrders'].append(current_user.buyOrders[id])

        if current_user.sellOrders != 'None':
            for id in current_user.sellOrders.keys():
                output['sellOrders'].append(current_user.sellOrders[id])

        if current_user.structureAccess != 'None':
            accessibleStructures = eveme.helper.getStructures(char_id)
            for i in range(len(accessibleStructures)):
                structure = eveme.helper.esiRequest('structureInfo', accessibleStructures[i], headers)
                accessibleStructures[i] = structure['name']
            output['structures'] = accessibleStructures

        # Get user wallet balance
        balance = eveme.helper.esiRequest('walletBalance', char_id, headers)
        output['walletBalance'] = balance
        output['walletTransactions'] = \
            eveme.helper.esiRequest('walletTransactions', char_id, headers)
        for transaction in output['walletTransactions']:
            transaction['item_name'] = invTypes[str(transaction['type_id'])]
    else:
        # Get the user's portrait and name
        output['name'] = public['name']
        output['profilePic'] = eveme.helper.esiRequest('portrait', char_id)['px256x256']

    return render_template("character.html", context=output)


@eveme.app.route("/callback/")
def callback():
    context = {}
    json_url = os.path.join(pathlib.Path().resolve(), "eveme/static/json", "invTypes.json")
    invTypes = dict(json.load(open(json_url)))
    code = request.args.get('code')

    user_pass = "{}:{}".format(current_app.config['ESI_CLIENT_ID'],
                               current_app.config['ESI_SECRET_KEY'])
    basic_auth = base64.urlsafe_b64encode(user_pass.encode('utf-8')).decode()
    auth_header = "Basic {}".format(basic_auth)
    form_values = {
        "grant_type": "authorization_code",
        "code": code,
    }

    headers = {"Authorization": auth_header}
    res = send_token_request(form_values, add_headers=headers)
    data = handle_sso_token_response(res)
    char_id = data['id']
    structuresChecked = {}
    user_info = {
        'accessToken': None,
        'buyOrders': {},
        'sellOrders': {},
        'name': None,
        'profilePic': None,
        'structureAccess': [],
    }

    headers = eveme.helper.createHeaders(data['access_token'])

    if data['orders']:
        for order in data['orders']:
            # eveme.helper.insertStructure(char_id, order['location_id'])
            # Format price with commas

            if order['location_id'] in structuresChecked.keys():
                structureOrders = structuresChecked[order['location_id']]
            else:
                structureOrdersQuery = ("https://esi.evetech.net/latest/markets/structures"
                                        "/{}/".format(order['location_id']))
                res = requests.get(structureOrdersQuery, headers=headers)
                res.raise_for_status()
                numPages = res.headers['X-Pages']
                structureOrders = res.json()

                for i in range(1, int(numPages)):
                    structureOrdersQuery = ("https://esi.evetech.net/latest/markets/structures"
                                            "/{}/?datasource=tranquility&page="
                                            "{}".format(order['location_id'], i + 1))
                    res = requests.get(structureOrdersQuery, headers=headers)
                    numPages = res.headers['X-Pages']
                    structureOrders.extend(res.json())
                structuresChecked[order['location_id']] = structureOrders

            # check each order with order in structure and compare
            if 'is_buy_order' in order.keys():
                order['itemName'] = invTypes[str(order['type_id'])]
                orderMaxPrice = -1.0
                for structOrder in structureOrders:
                    # bug here string indices?
                    if (structOrder['is_buy_order']) and (structOrder['type_id'] == order['type_id']):
                        if structOrder['price'] > orderMaxPrice:
                            orderMaxPrice = structOrder['price']
                order['structureHighest'] = orderMaxPrice
                order.pop('type_id', None)
                order.pop('location_id', None)
                user_info['buyOrders'][order['order_id']] = order
            else:
                order['itemName'] = invTypes[str(order['type_id'])]
                orderMinPrice = float('inf')
                for structOrder in structureOrders:
                    if (not structOrder['is_buy_order']) and (structOrder['type_id'] == order['type_id']):
                        if structOrder['price'] < orderMinPrice:
                            orderMinPrice = structOrder['price']
                order['structureLowest'] = orderMinPrice
                order.pop('type_id', None)
                order.pop('location_id', None)
                user_info['sellOrders'][order['order_id']] = order
        user_info['structureAccess'] = list(structuresChecked.keys())
    else:
        user_info['buyOrders'] = 'None'
        user_info['sellOrders'] = 'None'
        user_info['structureAccess'] = 'None'
    # Get the user's portrait
    portrait = eveme.helper.esiRequest('portrait', char_id)['px256x256']

    # Create a user in your db with the information provided
    # by ESI
    user_info['name'] = data['name']
    user_info['profilePic'] = portrait
    user_info['accessToken'] = data['access_token']

    user = User(
        id_=char_id, name_=data['name'], profilePic_=portrait,
        buyOrders_=user_info['buyOrders'], sellOrders_=user_info['sellOrders'],
        accessToken_=data['access_token'], structureAccess_=list(structuresChecked.keys())
    )

    login_user(user)
    # Doesn't exist? Add it to the database.
    if not User.get(char_id):
        User.create(user_info, char_id)
    User.update(user_info, char_id)
    return redirect(url_for('character', char_id=char_id))
