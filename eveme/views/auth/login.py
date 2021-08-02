"""
EVEME index (login) view.

URLs include:
/login/
/character/<char_id>
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
from eveme.shared_flow import handle_sso_token_response
from eveme.user import User
from firebase_admin import db
import eveme.helper
import eveme
import requests
import base64
import json
import os
import pathlib
import time


@eveme.app.route("/login/")
def login():
    start_time = time.time()
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
    print("--- login() took %s seconds ---" % (time.time() - start_time))
    return redirect(request_uri)


@eveme.app.route("/character/<char_id>")
def character(char_id):
    start_time = time.time()
    json_url = os.path.join(pathlib.Path().resolve(), "eveme/static/json", "invTypes.json")
    invTypes = dict(json.load(open(json_url)))

    output = {}
    inAlliance = False

    public = eveme.helper.esiRequest('charInfo', char_id)

    output['isLoggedInUser'] = False

    if current_user.is_authenticated and char_id == current_user.id:
        eveme.helper.refreshAuth()
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
        # Get user corp and alliance
        if current_user.alliance:
            output['alliance'] = current_user.alliance
        output['corporation'] = current_user.corporation

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
        # Get the user's corp and alliance
        corporation = eveme.helper.esiRequest('corpInfo', public['corporation_id'])

        if 'alliance_id' in public.keys():
            alliance = eveme.helper.esiRequest('allianceInfo', public['alliance_id'])
            inAlliance = True
            output['alliance'] = alliance['name']

        output['corporation'] = corporation['name']
    print("--- character() took %s seconds ---" % (time.time() - start_time))
    return render_template("character.html", context=output)


@eveme.app.route("/callback/")
def callback():
    start_time = time.time()
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
    res = eveme.helper.send_token_request(form_values, add_headers=headers)
    data = handle_sso_token_response(res)
    authTime = time.time()
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

    order_time = time.time()
    ref = db.reference('prices')
    if data['orders']:
        for order in data['orders']:
            # eveme.helper.insertStructure(char_id, order['location_id'])
            # Format price with commas

            if order['location_id'] not in structuresChecked.keys():
                structuresChecked[order['location_id']] = 1

            # check each order with order in structure and compare
            if 'is_buy_order' in order.keys():
                order['itemName'] = invTypes[str(order['type_id'])]
                order['structureHighest'] = ref.child('buy').child(str(order['type_id'])).get()
                order.pop('type_id', None)
                order.pop('location_id', None)
                user_info['buyOrders'][order['order_id']] = order
            else:
                order['itemName'] = invTypes[str(order['type_id'])]
                order['structureLowest'] = ref.child('sell').child(str(order['type_id'])).get()
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

    # Get the user's corporation and alliance
    corporation = eveme.helper.esiRequest('corpInfo', data['corporation_id'])

    if 'alliance_id' in data.keys():
        alliance = eveme.helper.esiRequest('allianceInfo', data['alliance_id'])
        inAlliance = True
        user_info['alliance'] = alliance['name']
    print("--- orders processing took %s seconds ---" % (time.time() - order_time))
    user_info['corporation'] = corporation['name']

    # Create a user in your db with the information provided
    # by ESI
    user_info['name'] = data['name']
    user_info['profilePic'] = portrait
    user_info['accessToken'] = data['access_token']
    user_info['refreshToken'] = data['refresh_token']
    user_info['authTime'] = authTime

    user = User(
        id_=char_id, name_=data['name'], profilePic_=portrait,
        buyOrders_=user_info['buyOrders'], sellOrders_=user_info['sellOrders'],
        accessToken_=data['access_token'], structureAccess_=list(structuresChecked.keys()),
        corporation_=corporation['name'], alliance_=alliance['name'], authTime_=authTime,
        refreshToken_=data['refresh_token']
    )

    login_user(user)
    # Doesn't exist? Add it to the database.
    if not User.get(char_id):
        User.create(user_info, char_id)
    User.update(user_info, char_id)

    print("--- callback() took %s seconds ---" % (time.time() - start_time))

    return redirect(url_for('character', char_id=char_id))
