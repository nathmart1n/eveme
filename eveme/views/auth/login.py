"""
EVEME login view.

URLs include:
/login/
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
                structuresChecked[order['location_id']] = eveme.helper.esiRequest('structureInfo', order['location_id'], headers)['name']

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
        user_info['structureAccess'] = structuresChecked
    else:
        user_info['buyOrders'] = 'None'
        user_info['sellOrders'] = 'None'
        user_info['structureAccess'] = 'None'

    print("--- orders processing took %s seconds ---" % (time.time() - order_time))

    # Create a user in your db with the information provided
    # by ESI
    user_info['accessToken'] = data['access_token']
    user_info['refreshToken'] = data['refresh_token']
    user_info['authTime'] = authTime

    user = User(
        id_=char_id, accessToken_=data['access_token'],
        authTime_=authTime, refreshToken_=data['refresh_token'],
        name_=data['name'], profilePic_=eveme.helper.esiRequest('portrait', char_id)['px256x256']
    )
    login_user(user)
    # Doesn't exist? Add it to the database.
    if not User.get(char_id):
        eveme.helper.updateUserData()
    User.update(user_info, char_id)

    print("--- callback() took %s seconds ---" % (time.time() - start_time))

    return redirect(url_for('character', char_id=char_id))
