import eveme
import requests
import time
from firebase_admin import db, credentials


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
    start_time = time.time()
    """Performs request to ESI API. userToken necessary if request type requires auth."""
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
