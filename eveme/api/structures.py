"""REST API for structures."""
import flask
import eveme
from flask_login import current_user


@eveme.app.route('/api/v1/p/<int:char_id>/likes/',
                 methods=["GET", "DELETE", "POST"])
def get_structures(char_id):
    """Return likes on postid.

    Example:
    {
      "logname_likes_this": 1,
      "likes_count": 3,
      "postid": 1,
      "url": "/api/v1/p/1/likes/"
    }
    """
    if not (current_user.is_authenticated and char_id == current_user.id):
        return flask.abort(403)

    connection = eveme.model.get_db()

    if flask.request.method == 'POST':
        cur = connection.execute(
            "SELECT 1 "
            "FROM likes "
            "WHERE (owner = ? AND postid = ?)",
            (user, postid_url_slug,)
        )
        is_in_likes = cur.fetchone()

        if not is_in_likes:
            connection.execute(
                "INSERT INTO likes "
                "(owner, postid) "
                "VALUES (? , ?)",
                (user, postid_url_slug,)
            )

            like_data = {
                "logname": user,
                "postid": postid_url_slug
            }

            return flask.jsonify(like_data), 201

        error_data = {
          "logname": user,
          "message": "Conflict",
          "postid": postid_url_slug,
          "status_code": 409
        }

        return flask.jsonify(error_data), 409
    if flask.request.method == 'DELETE':
        connection.execute(
            "DELETE FROM likes "
            "WHERE (owner, postid) = (?, ?)",
            (user, postid_url_slug,)
        )
        return '', 204

    context = {
      "logname_likes_this": 0,
      "likes_count": 0,
      "postid": postid_url_slug,
      "url": "/api/v1/p/" + str(postid_url_slug) + "/likes/"
    }

    cur = connection.execute(
        "SELECT 1 "
        "FROM likes "
        "WHERE (owner = ? AND postid = ?)",
        (user, postid_url_slug,)
    )
    is_in_likes = cur.fetchone()

    cur = connection.execute(
        "SELECT COUNT(1) "
        "FROM likes "
        "WHERE postid = ?",
        (postid_url_slug,)
    )
    matching_likes = cur.fetchall()

    if is_in_likes:
        context["logname_likes_this"] = 1

    context["likes_count"] = matching_likes[0]['COUNT(1)']

    return flask.jsonify(**context)
