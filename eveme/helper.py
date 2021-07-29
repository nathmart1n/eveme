import eveme
import requests
import time
from firebase_admin import db
from flask_login import current_user


def createHeaders(access_token):
    return {
            "Authorization": "Bearer {}".format(access_token)
           }


def getStructures(user_id):
    ref = db.reference('users/' + user_id)
    output = []
    structs = ref.get()['structureAccess']
    for structure in structs:
        output.append(structure)
    return output


def insertStructure(user_id, structure_id):
    ref = db.reference('users/' + user_id + '/structureAccess')
    ref.put(structure_id)


def esiRequest(requestType, variable, charHeaders=None):
    """Performs request to ESI API. userToken necessary if request type requires auth."""
    start_time = time.time()
    requestURL = {
        'charInfo': "https://esi.evetech.net/latest/characters/{}/".format(variable),
        'charOrders': "https://esi.evetech.net/latest/characters/{}/orders/".format(variable),
        'corpInfo': "https://esi.evetech.net/latest/corporations/{}/".format(variable),
        'allianceInfo': "https://esi.evetech.net/latest/alliances/{}/".format(variable),
        'structureInfo': "https://esi.evetech.net/latest/universe/structures/{}/".format(variable),
        'walletBalance': "https://esi.evetech.net/latest/characters/{}/wallet".format(variable),
        'portrait': "https://esi.evetech.net/latest/characters/{}/portrait/".format(variable),
        'walletTransactions': "https://esi.evetech.net/latest/characters/{}/wallet/transactions".format(variable),
        'stationInfo': "https://esi.evetech.net/latest/universe/stations/{}/".format(variable),
    }

    if charHeaders:
        res = requests.get(requestURL[requestType], headers=charHeaders)
    else:
        res = requests.get(requestURL[requestType])

    print("--- esiRequest() with " + requestType + " took %s seconds ---" % (time.time() - start_time))
    return res.json()


def updateUserData():
    """Queries ESI and updates user's publicData in DB."""
    start_time = time.time()
    # Get current user id
    char_id = current_user.id
    # Dict for new info
    new = {}
    # Get public data
    publicData = eveme.helper.esiRequest('charInfo', char_id)

    # Get portrait
    portrait = eveme.helper.esiRequest('portrait', char_id)

    # Get the user's corporation and alliance
    corporation = eveme.helper.esiRequest('corpInfo', publicData['corporation_id'])

    if 'alliance_id' in publicData.keys():
        alliance = eveme.helper.esiRequest('allianceInfo', publicData['alliance_id'])
        inAlliance = True
        new['alliance'] = alliance['name']

    # Adding our new info
    new['corporation'] = corporation['name']
    new['name'] = publicData['name']
    new['profilePic'] = portrait['px256x256']
    ref = db.reference('users')
    char_ref = ref.child(char_id)
    char_ref.update(new)
    print("--- updateUserData() with took %s seconds ---" % (time.time() - start_time))
    return None


def updateUserOrders():
    """Queries ESI and updates user's market orders in DB."""
    return None


def updatePriceData():
    """Queries ESI data for structures user has orders in and updates max/min prices."""
    return None
