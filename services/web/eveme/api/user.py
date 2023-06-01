"""REST API for structures."""
import flask
import eveme
from flask_login import current_user
from firebase_admin import db


@eveme.app.route('/api/v1/u/<char_id>/',
                 methods=["GET", "DELETE", "POST"])
def get_user(char_id):
    """Returns data held on user.

    Example:
    {
      "url": "/api/v1/u/96616254/"
    }
    """
    if not (current_user.is_authenticated and char_id == current_user.id):
        return flask.abort(403)

    # connection = eveme.model.get_db()

    if flask.request.method == 'POST':
        print('Post!')
    if flask.request.method == 'DELETE':
        print('Delete!')

    ref = db.reference('users')
    context = ref.child(char_id).get()

    context['url'] = "/api/v1/u/" + char_id + "/"

    return flask.jsonify(**context)
