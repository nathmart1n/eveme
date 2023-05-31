"""
EVEME imports view.

URLs include:
/imports/
"""
import flask
import eveme
import eveme.helper
import requests
import os
import pathlib
import json
import time
import datetime
from flask_login import current_user
from firebase_admin import db


@eveme.app.route('/stationtrading/', methods=['GET', 'POST'])
def show_station_trading():
    """Display / route."""
    if current_user.is_authenticated:
        eveme.helper.refreshAuth()
    return flask.render_template("station_trading.html")
