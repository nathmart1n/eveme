"""REST API for main."""
import flask
import eveme


@eveme.app.route('/api/v1/', methods=["GET"])
def get_info():
    """Return general info as below.

    Example:
    {
      "user": "/api/v1/u/",
      "url": "/api/v1/"
    }
    """
    context = {
      "user": "/api/v1/u/",
      "url": "/api/v1/"
    }
    return flask.jsonify(**context)
