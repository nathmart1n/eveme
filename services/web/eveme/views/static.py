"""
EVEME static file serving

URLs include:
/static/<path:filename>
"""
from flask import send_from_directory
import eveme


@eveme.app.route("/static/<path:filename>")
def staticfiles(filename):
    return send_from_directory(eveme.app.config["STATIC_FOLDER"], filename)
