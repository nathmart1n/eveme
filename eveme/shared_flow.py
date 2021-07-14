"""Contains all shared OAuth 2.0 flow functions for examples

This module contains all shared functions between the two different OAuth 2.0
flows recommended for web based and mobile/desktop applications. The functions
found here are used by the OAuth 2.0 examples contained in this project.
"""
import urllib

import requests

from eveme.validate_jwt import validate_eve_jwt


def send_token_request(form_values, add_headers={}):
    """Sends a request for an authorization token to the EVE SSO.

    Args:
        form_values: A dict containing the form encoded values that should be
                     sent with the request
        add_headers: A dict containing additional headers to send
    Returns:
        requests.Response: A requests Response object
    """

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Host": "login.eveonline.com",
    }

    if add_headers:
        headers.update(add_headers)

    res = requests.post(
        "https://login.eveonline.com/v2/oauth/token",
        data=form_values,
        headers=headers,
    )

    res.raise_for_status()

    return res


def handle_sso_token_response(sso_response):
    """Handles the authorization code response from the EVE SSO.

    Args:
        sso_response: A requests Response object gotten by calling the EVE
                      SSO /v2/oauth/token endpoint
    """

    if sso_response.status_code == 200:
        data = sso_response.json()
        access_token = data["access_token"]

        # print("\nVerifying access token JWT...")

        jwt = validate_eve_jwt(access_token)
        # print(jwt)
        character_id = jwt["sub"].split(":")[2]
        character_name = jwt["name"]
        publicData_path = ("https://esi.evetech.net/latest/characters/{}"
                           "/".format(character_id))

        headers = {
            "Authorization": "Bearer {}".format(access_token)
        }

        res = requests.get(publicData_path)

        res.raise_for_status()

        data = res.json()
        data["id"] = character_id

        ordersQuery = ("https://esi.evetech.net/latest/characters/{}"
                       "/orders/".format(character_id))

        res = requests.get(ordersQuery, headers=headers)
        orders = res.json()
        data['orders'] = orders

        for order in data['orders']:
            structureName = ("https://esi.evetech.net/latest/universe/structures"
                             "/{}/".format(order['location_id']))
            res = requests.get(structureName, headers=headers)
            structure = res.json()
            order['structure_name'] = structure['name']

        return data
    else:
        print("\nSomething went wrong! Re read the comment at the top of this "
              "file and make sure you completed all the prerequisites then "
              "try again. Here's some debug info to help you out:")
        print("\nSent request with url: {} \nbody: {} \nheaders: {}".format(
            sso_response.request.url,
            sso_response.request.body,
            sso_response.request.headers
        ))
        print("\nSSO response code is: {}".format(sso_response.status_code))
        print("\nSSO response JSON is: {}".format(sso_response.json()))
        return -1
