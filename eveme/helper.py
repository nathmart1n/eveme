import eveme
import requests


def createHeaders(access_token):
    """Formats headers for ESI API authenticated request."""
    return {
            "Authorization": "Bearer {}".format(access_token)
           }


def getStructures(char_id):
    """Gets all structures for a given character."""
    connection = eveme.model.get_db()

    structures = connection.execute(
        "SELECT * FROM structureAccess WHERE id = ?", (char_id,)
    ).fetchall()

    return [x['structure_id'] for x in structures]


def insertStructure(user_id, structure_id):
    """Inserts structure into structureAccess table."""
    connection = eveme.model.get_db()
    connection.execute(
        "INSERT OR IGNORE INTO structureAccess (id, structure_id) "
        "VALUES (?, ?)",
        (user_id, structure_id),
    )
    connection.commit()


def esiRequest(requestType, variable, charHeaders=None):
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
    }

    if charHeaders:
        res = requests.get(requestURL[requestType], headers=charHeaders)
    else:
        res = requests.get(requestURL[requestType])
    return res.json()
