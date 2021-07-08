import re
import base64
import requests
import os
import json
import sqlite3
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
from user import User
from db import init_db_command

from shared_flow import send_token_request
from shared_flow import handle_sso_token_response

app = Flask(__name__)

login_manager = LoginManager()
login_manager.init_app(app)

# Naive database setup
try:
    init_db_command()
except sqlite3.OperationalError:
    # Assume it's already been created
    pass

load_dotenv()
ESI_SECRET_KEY = os.environ.get("ESI_API_SECRET_KEY", None)
ESI_CLIENT_ID = os.environ.get("ESI_CLIENT_ID", None)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", None)


@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)


@app.route("/")
def home():
    return render_template("home.html", value=ESI_CLIENT_ID)


@app.route("/about/")
def about():
    return render_template("about.html")


@app.route("/contact/")
def contact():
    return render_template("contact.html")


@app.route("/login/")
def login():
    request_uri = 'https://login.eveonline.com/v2/oauth/authorize/?response' +\
                  '_type=code&redirect_uri=http%3A%2F%2Flocalhost%3A5000%2F' +\
                  'callback%2F&client_id=' + ESI_CLIENT_ID + '&scope=public' +\
                  'Data&state=ohd9912dn102dn012'
    return redirect(request_uri)


@app.route("/success/<char_id>")
def success(char_id):

    tempQuery = ("https://esi.evetech.net/latest/characters/{}"
                 "/".format(char_id))

    res = requests.get(tempQuery)
    public = res.json()

    # pull profile pic from user db entry?

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
    # output['portrait'] =

    return render_template("success.html", context=output)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("home"))


@app.route("/callback/")
def callback():
    context = {}

    code = request.args.get('code')

    user_pass = "{}:{}".format(ESI_CLIENT_ID, ESI_SECRET_KEY)
    basic_auth = base64.urlsafe_b64encode(user_pass.encode('utf-8')).decode()
    auth_header = "Basic {}".format(basic_auth)

    form_values = {
        "grant_type": "authorization_code",
        "code": code,
    }

    headers = {"Authorization": auth_header}
    res = send_token_request(form_values, add_headers=headers)

    data = handle_sso_token_response(res)
    char_id = data['id']

    tempQuery = ("https://esi.evetech.net/latest/characters/{}"
                 "/portrait/".format(char_id))

    res = requests.get(tempQuery)
    portrait = res.json()
    picture = portrait['px64x64']

    # Create a user in your db with the information provided
    # by ESI
    user = User(
        id_=char_id, name=data['name'], profile_pic=picture
    )

    # Doesn't exist? Add it to the database.
    if not User.get(char_id):
        User.create(char_id, data['name'], picture)

    # Begin user session by logging the user in
    login_user(user)

    return redirect(url_for("success", char_id=char_id))
    # return render_template("callback.html", context=data)
