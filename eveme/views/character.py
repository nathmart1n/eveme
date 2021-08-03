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
