from flask import Flask, render_template, request
from datetime import datetime
from dotenv import load_dotenv
import re
import base64
import requests
import os
import json

from shared_flow import send_token_request
from shared_flow import handle_sso_token_response

app = Flask(__name__)

load_dotenv()
app.secret_key = os.environ.get("ESI_API_SECRET_KEY")
client_id = os.environ.get("ESI_CLIENT_ID")


@app.route("/")
def home():
    print(client_id)
    return render_template("home.html", value=client_id)


@app.route("/about/")
def about():
    return render_template("about.html")


@app.route("/contact/")
def contact():
    return render_template("contact.html")


@app.route("/callback/")
def callback():
    context = {}

    code = request.args.get('code')

    user_pass = "{}:{}".format(client_id, app.secret_key)
    basic_auth = base64.urlsafe_b64encode(user_pass.encode('utf-8')).decode()
    auth_header = "Basic {}".format(basic_auth)

    form_values = {
        "grant_type": "authorization_code",
        "code": code,
    }

    headers = {"Authorization": auth_header}
    res = send_token_request(form_values, add_headers=headers)

    data = handle_sso_token_response(res)

    print(data)
    # get alliance data
    allianceQuery = ("https://esi.evetech.net/latest/alliances/{}"
                     "/".format(data['alliance_id']))
    res = requests.get(allianceQuery)
    alliance = res.json()
    print(alliance)

    # get corp data
    corpQuery = ("https://esi.evetech.net/latest/corporations/{}"
                 "/".format(data['corporation_id']))
    res = requests.get(corpQuery)
    corp = res.json()
    print(corp)

    context['name'] = data['name']
    context['alliance_name'] = alliance['name']
    context['corporation_name'] = corp['name']

    # let user click on alliance and corp name and be directed to pages

    return render_template("callback.html", context=context)
