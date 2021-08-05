"""
EVEME character view.

URLs include:
/character/<char_id>
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
from eveme import user
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


@eveme.app.route("/character/<char_id>")
def character(char_id):
    start_time = time.time()
    json_url = os.path.join(pathlib.Path().resolve(), "eveme/static/json", "invTypes.json")
    invTypes = dict(json.load(open(json_url)))

    ref = db.reference('users')

    output = {}
    inAlliance = False

    public = eveme.helper.esiRequest('charInfo', char_id)

    output['isLoggedInUser'] = False

    if current_user.is_authenticated and char_id == current_user.id:
        user_ref = ref.child(char_id).get()
        eveme.helper.refreshAuth()
        output['isLoggedInUser'] = True
        headers = eveme.helper.createHeaders(user_ref['accessToken'])
        output['name'] = user_ref['name']
        output['profilePic'] = user_ref['profilePic']

        if user_ref['structureAccess'] != 'None':
            output['structures'] = user_ref['structureAccess']
        # Get user corp and alliance
        if user_ref['alliance']:
            output['alliance'] = user_ref['alliance']
        output['corporation'] = user_ref['corporation']

        # Get user wallet balance
        output['walletBalance'] = user_ref['walletBalance']
        output['walletTransactions'] = user_ref['walletTransactions']
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
