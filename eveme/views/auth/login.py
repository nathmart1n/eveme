"""
EVEME index (login) view.

URLs include:
/login/
/success/<char_id>
/callback/
"""
from flask import (
    Flask,
    current_app,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import login_user, current_user
from eveme.shared_flow import send_token_request, handle_sso_token_response
from eveme.user import User
import eveme
import requests
import base64
import json


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

    if current_user.is_authenticated and char_id == current_user.id:
        buyOrders = current_user.buyOrders.split('},{')
        sellOrders = current_user.sellOrders.split('},{')
        buyOrdersDicts = []
        sellOrdersDicts = []
        for i in range(len(buyOrders)):
            if i == 0:
                buyOrders[i] = buyOrders[i]+'}'
            elif i == len(buyOrders) - 1:
                buyOrders[i] = '{'+buyOrders[i]
            else:
                buyOrders[i] = '{'+buyOrders[i]+'}'
            # print(buyOrders[i])
            buyOrdersDicts.append(json.loads(buyOrders[i]))
        for i in range(len(sellOrders)):
            if i == 0:
                sellOrders[i] = sellOrders[i]+'}'
            elif i == len(sellOrders) - 1:
                sellOrders[i] = '{'+sellOrders[i]
            else:
                sellOrders[i] = '{'+sellOrders[i]+'}'
            # print(sellOrders[i])
            sellOrdersDicts.append(json.loads(sellOrders[i]))
        # print(buyOrders[0])
        output['name'] = current_user.name
        output['profile_pic'] = current_user.profile_pic
        output['buyOrders'] = buyOrdersDicts
        output['sellOrders'] = sellOrdersDicts
        output['isLoggedInUser'] = True

    else:
        tempQuery = ("https://esi.evetech.net/latest/characters/{}"
                     "/portrait/".format(char_id))

        res = requests.get(tempQuery)
        portrait = res.json()

        output['name'] = public['name']
        output['profile_pic'] = portrait['px64x64']

    return render_template("character.html", context=output)


@eveme.app.route("/callback/")
def callback():
    context = {}

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

    # print(data['orders'])
    userBuyOrders = []
    userSellOrders = []

    for order in data['orders']:
        itemName = ("https://esi.evetech.net/latest/universe/types"
                    "/{}/".format(order['type_id']))

        res = requests.get(itemName)
        item = res.json()
        if 'is_buy_order' in order.keys():
            order['name'] = item['name']
            userBuyOrders.append(json.dumps(order))
        else:
            order['name'] = item['name']
            userSellOrders.append(json.dumps(order))

    portraitQuery = ("https://esi.evetech.net/latest/characters/{}"
                     "/portrait/".format(char_id))

    res = requests.get(portraitQuery)
    portrait = res.json()
    picture = portrait['px64x64']

    # Create a user in your db with the information provided
    # by ESI

    # print(userSellOrders, userBuyOrders)
    buyOrders = ','.join(userBuyOrders)
    sellOrders = ','.join(userSellOrders)
    user = User(
        id_=char_id, name=data['name'], profile_pic=picture,
        buyOrders=buyOrders, sellOrders=sellOrders,
    )
    # print(user.buyOrders)
    login_user(user)
    # Doesn't exist? Add it to the database.
    if not User.get(char_id):
        User.create(
            char_id, data['name'], picture, buyOrders, sellOrders
        )
    # Exists but changed name or profile picture
    else:
        User.update(
            char_id, data['name'], picture, buyOrders, sellOrders
        )

    return redirect(url_for('character', char_id=char_id))
