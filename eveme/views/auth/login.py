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
from flask_login import login_user
from eveme.shared_flow import send_token_request, handle_sso_token_response
from eveme.user import User
import eveme
import requests
import base64


@eveme.app.route("/login/")
def login():
    """First step in ESI OAuth."""
    print(current_app.config['ESI_CLIENT_ID'])
    request_uri = 'https://login.eveonline.com/v2/oauth/authorize/?response' +\
                  '_type=code&redirect_uri=http%3A%2F%2Flocalhost%3A5000%2F' +\
                  'callback%2F&client_id=' +\
                  current_app.config['ESI_CLIENT_ID'] + '&scope=public' +\
                  'Data&state=ohd9912dn102dn012'
    return redirect(request_uri)


@eveme.app.route("/success/<char_id>")
def success(char_id):

    tempQuery = ("https://esi.evetech.net/latest/characters/{}"
                 "/".format(char_id))

    res = requests.get(tempQuery)
    public = res.json()

    # pull profile pic from user db entry?

    tempQuery = ("https://esi.evetech.net/latest/alliances/{}"
                 "/".format(public['alliance_id']))

    res = requests.get(tempQuery)
    alliance = res.json()

    tempQuery = ("https://esi.evetech.net/latest/corporations/{}"
                 "/".format(public['corporation_id']))

    res = requests.get(tempQuery)
    corporation = res.json()

    output = {}

    output['name'] = public['name']
    output['alliance_name'] = alliance['name']
    output['corp_name'] = corporation['name']
    # output['portrait'] =

    return render_template("success.html", context=output)


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

    tempQuery = ("https://esi.evetech.net/latest/characters/{}"
                 "/portrait/".format(char_id))

    res = requests.get(tempQuery)
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

    # Begin user session by logging the user in
    login_user(user)

    return redirect(url_for("success", char_id=char_id))
    # return render_template("callback.html", context=data)
