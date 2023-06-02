"""
EVEME static handling.

URLs include:
/static/<path:filename>
"""
from flask import Flask, current_app, send_from_directory
import eveme


@eveme.app.route("/static/<path:filename>")
def staticfiles(filename):
    """Show requested static file."""
    return send_from_directory(current_app.config["STATIC_FOLDER"], filename)
