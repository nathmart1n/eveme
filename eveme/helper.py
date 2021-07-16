def createHeaders(access_token):
    return {
            "Authorization": "Bearer {}".format(access_token)
           }
