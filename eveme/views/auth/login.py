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
                  'esi-assets.read_assets.v1' +\
                  '&state=ohd9912dn102dn012'
    return redirect(request_uri)


@eveme.app.route("/character/<char_id>")
def character(char_id):
    output = {}
    inAlliance = False

    tempQuery = ("https://esi.evetech.net/latest/characters/{}"
                 "/".format(char_id))

    res = requests.get(tempQuery)
    public = res.json()

    tempQuery = ("https://esi.evetech.net/latest/corporations/{}"
                 "/".format(public['corporation_id']))

    res = requests.get(tempQuery)
    corporation = res.json()

    if 'alliance_id' in public.keys():
        tempQuery = ("https://esi.evetech.net/latest/alliances/{}"
                     "/".format(public['alliance_id']))

        res = requests.get(tempQuery)
        alliance = res.json()
        inAlliance = True

    output['corp_name'] = corporation['name']
    if inAlliance:
        output['alliance_name'] = alliance['name']

    output['isLoggedInUser'] = False

    print(type(current_user.id))

    if current_user.is_authenticated and char_id == current_user.id:
        headers = eveme.helper.createHeaders(current_user.accessToken)
        output['name'] = current_user.name
        output['profilePic'] = current_user.profilePic
        output['buyOrders'] = []
        output['sellOrders'] = []
        for id in current_user.buyOrders.keys():
            output['buyOrders'].append(current_user.buyOrders[id])
        for id in current_user.sellOrders.keys():
            output['sellOrders'].append(current_user.sellOrders[id])
        accessibleStructures = eveme.helper.getStructures(char_id)
        print(accessibleStructures)
        for i in range(len(accessibleStructures)):
            structureName = ("https://esi.evetech.net/latest/universe/structures"
                             "/{}/".format(accessibleStructures[i]))
            res = requests.get(structureName, headers=headers)
            structure = res.json()
            accessibleStructures[i] = structure['name']
        output['structures'] = accessibleStructures
        output['isLoggedInUser'] = True

    else:
        tempQuery = ("https://esi.evetech.net/latest/characters/{}"
                     "/portrait/".format(char_id))

        res = requests.get(tempQuery)
        portrait = res.json()

        output['name'] = public['name']
        output['profilePic'] = portrait['px64x64']

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
    orderKeys = ['']
    user_info = {
        char_id: {
            'accessToken': None,
            'buyOrders': {},
            'sellOrders': {},
            'name': None,
            'profilePic': None,
            'structureAccess': [],
        }
    }

    headers = eveme.helper.createHeaders(data['access_token'])

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
            user_info[char_id]['buyOrders'][order['order_id']] = order
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
            user_info[char_id]['sellOrders'][order['order_id']] = order
    portraitQuery = ("https://esi.evetech.net/latest/characters/{}"
                     "/portrait/".format(char_id))
    res = requests.get(portraitQuery)
    portrait = res.json()
    picture = portrait['px256x256']

    # Create a user in your db with the information provided
    # by ESI

    user_info[char_id]['name'] = data['name']
    user_info[char_id]['profilePic'] = picture
    user_info[char_id]['accessToken'] = data['access_token']
    user_info[char_id]['structureAccess'] = list(structuresChecked.keys())

    user = User(
        id_=char_id, name_=data['name'], profilePic_=picture,
        buyOrders_=user_info[char_id]['buyOrders'], sellOrders_=user_info[char_id]['sellOrders'],
        accessToken_=data['access_token'], structureAccess_=list(structuresChecked.keys())
    )

    login_user(user)
    # Doesn't exist? Add it to the database.
    if not User.get(char_id):
        User.create(user_info)
    # Exists but changed name or profile picture
    else:
        User.update(user_info)
    return redirect(url_for('character', char_id=char_id))
