"""
EVEME character view.

URLs include:
/character/<char_id>
"""
from flask import (
    render_template,
)
from flask_login import current_user
from firebase_admin import db
import eveme.helper
import eveme
import time


@eveme.app.route("/character/<char_id>")
def character(char_id):
    start_time = time.time()

    ref = db.reference('users')

    output = {}

    public = eveme.helper.esiRequest('charInfo', char_id)

    output['isLoggedInUser'] = False

    if current_user.is_authenticated and char_id == current_user.id:
        user_ref = ref.child(char_id).get()
        eveme.helper.refreshAuth()
        output['isLoggedInUser'] = True
        output['name'] = user_ref['name']
        output['profilePic'] = user_ref['profilePic']

        if 'structureAccess' in user_ref.keys():
            output['structures'] = user_ref['structureAccess']
        # Get user corp and alliance
        if 'alliance' in user_ref.keys():
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
            output['alliance'] = alliance['name']

        output['corporation'] = corporation['name']
    print("--- character() took %s seconds ---" % (time.time() - start_time))
    return render_template("character.html", context=output)
