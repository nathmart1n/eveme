"""REST API for main."""
import flask
import eveme


@eveme.app.route('/api/v1/', methods=["GET"])
def get_info():
    """Return general info as below.

    Example:
    {
      "structures": "/api/v1/s/",
      "url": "/api/v1/"
    }
    """
    context = {
      "structures": "/api/v1/s/",
      "url": "/api/v1/"
    }
    return flask.jsonify(**context)
