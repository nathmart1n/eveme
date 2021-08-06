"""
EVEME imports view.

URLs include:
/imports/
"""
import flask
import eveme
import eveme.helper
from flask_login import current_user
from firebase_admin import db


@eveme.app.route('/imports/', methods=['GET', 'POST'])
def show_imports():
    """Display /imports/ route."""

    context = {}
    context['isPost'] = False

    if flask.request.method == 'POST':
        context['isPost'] = True
        return flask.render_template("imports.html", context=context)

    context['structures'] = db.reference('users/' + current_user.id + '/structureAccess').get()

    if current_user.is_authenticated:
        eveme.helper.refreshAuth()
    return flask.render_template("imports.html", context=context)
