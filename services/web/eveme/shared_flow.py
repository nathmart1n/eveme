"""Contains all shared OAuth 2.0 flow functions for examples

This module contains all shared functions between the two different OAuth 2.0
flows recommended for web based and mobile/desktop applications. The functions
found here are used by the OAuth 2.0 examples contained in this project.
"""
import eveme.helper
import time
import eveme

from eveme.validate_jwt import validate_eve_jwt


def handle_sso_token_response(sso_response):
    start_time = time.time()
    """Handles the authorization code response from the EVE SSO.

    Args:
        sso_response: A requests Response object gotten by calling the EVE
                      SSO /v2/oauth/token endpoint
    """

    if sso_response.status_code == 200:
        data = sso_response.json()
        # eveme.app.logger.info(data)
        access_token = data["access_token"]
        refresh_token = data['refresh_token']

        # eveme.app.logger.info("\nVerifying access token JWT...")
        jwt = validate_eve_jwt(access_token)
        # eveme.app.logger.info(jwt)
        character_id = int(jwt["sub"].split(":")[2])
        data = eveme.helper.esiRequest('charInfo', character_id)

        data['access_token'] = access_token
        data['refresh_token'] = refresh_token
        data["id"] = character_id

        eveme.app.logger.info("--- handle_sso_token_response() took %s seconds ---" % (time.time() - start_time))
        return data
    else:
        eveme.app.logger.info("\nSomething went wrong! Re read the comment at the top of this "
                              "file and make sure you completed all the prerequisites then "
                              "try again. Here's some debug info to help you out:")
        eveme.app.logger.info("\nSent request with url: {} \nbody: {} \nheaders: {}".format(
            sso_response.request.url,
            sso_response.request.body,
            sso_response.request.headers
        ))
        eveme.app.logger.info("\nSSO response code is: {}".format(sso_response.status_code))
        eveme.app.logger.info("\nSSO response JSON is: {}".format(sso_response.json()))
        return -1
