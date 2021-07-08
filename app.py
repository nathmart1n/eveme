from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime
from dotenv import load_dotenv
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)
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
ESI_CLIENT_ID = os.environ.get("ESI_CLIENT_ID", None)


@app.route("/")
def home():
    return render_template("home.html", value=ESI_CLIENT_ID)


@app.route("/about/")
def about():
    return render_template("about.html")


@app.route("/contact/")
def contact():
    return render_template("contact.html")


@app.route("/success/<char_id>")
def success(char_id):

    tempQuery = ("https://esi.evetech.net/latest/characters/{}"
                 "/".format(char_id))

    res = requests.get(tempQuery)
    public = res.json()

    tempQuery = ("https://esi.evetech.net/latest/alliances/{}"
                 "/".format(public['alliance_id']))

    res = requests.get(tempQuery)
    alliance = res.json()

    tempQuery = ("https://esi.evetech.net/latest/corporations/{}"
                 "/".format(public['corporation_id']))

    res = requests.get(tempQuery)
    corporation = res.json()

    output = {}

    output['name'] = public['name']
    output['alliance_name'] = alliance['name']
    output['corp_name'] = corporation['name']

    return render_template("success.html", context=output)


@app.route("/callback/")
def callback():
    context = {}

    code = request.args.get('code')

    user_pass = "{}:{}".format(ESI_CLIENT_ID, app.secret_key)
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
    char_id = data['id']

    return redirect(url_for("success", char_id=char_id))
    # return render_template("callback.html", context=data)
