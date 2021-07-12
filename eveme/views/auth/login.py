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

    if current_user.is_authenticated and char_id == current_user.id:
        output['name'] = current_user.name
        output['profile_pic'] = current_user.profile_pic

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
    userOrders = []

    for order in data['orders']:
        itemName = ("https://esi.evetech.net/latest/universe/types"
                    "/{}/".format(order['type_id']))

        res = requests.get(itemName)
        item = res.json()
        if 'is_buy_order' in order.keys():
            print('Buy:', item['name'])
        else:
            print('Sell:', item['name'])

    portraitQuery = ("https://esi.evetech.net/latest/characters/{}"
                     "/portrait/".format(char_id))

    res = requests.get(portraitQuery)
    portrait = res.json()
    picture = portrait['px64x64']

    # Create a user in your db with the information provided
    # by ESI
    user = User(
        id_=char_id, name=data['name'], profile_pic=picture
    )

    # Doesn't exist? Add it to the database.
    if not User.get(char_id):
        User.create(char_id, data['name'], picture)
    # Exists but changed name or profile picture
    elif (User.get(char_id).name != data['name'] or User.get(char_id).profile_pic != picture):
        User.update(char_id, data['name'], picture)

    # Begin user session by logging the user in
    login_user(user)

    return redirect(url_for("character", char_id=char_id))
    # return render_template("callback.html", context=data)
