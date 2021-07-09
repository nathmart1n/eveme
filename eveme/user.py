from flask_login import UserMixin

import eveme


class User(UserMixin):
    def __init__(self, id_, name, profile_pic):
        self.id = id_
        self.name = name
        self.profile_pic = profile_pic

    @staticmethod
    def get(user_id):
        connection = eveme.model.get_db()

        user = connection.execute(
            "SELECT * FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        if not user:
            return None
        user = User(
            id_=user['id'], name=user['name'], profile_pic=user['profile_pic']
        )
        return user

    @staticmethod
    def create(id_, name, profile_pic):
        connection = eveme.model.get_db()
        connection.execute(
            "INSERT INTO users (id, name, profile_pic) "
            "VALUES (?, ?, ?)",
            (id_, name, profile_pic),
        )
        connection.commit()
