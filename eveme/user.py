from flask_login import UserMixin

import eveme


class User(UserMixin):
    def __init__(self, id_, name, profile_pic, buyOrders, sellOrders):
        self.id = id_
        self.name = name
        self.profile_pic = profile_pic
        self.buyOrders = buyOrders
        self.sellOrders = sellOrders

    @staticmethod
    def get(user_id):
        connection = eveme.model.get_db()

        user = connection.execute(
            "SELECT * FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        if not user:
            return None
        user = User(
            id_=user['id'], name=user['name'], profile_pic=user['profile_pic'],
            buyOrders=user['buyOrders'], sellOrders=user['sellOrders']
        )
        return user

    @staticmethod
    def update(id_, name, profile_pic, buyOrders, sellOrders):
        connection = eveme.model.get_db()
        sql = ''' UPDATE users
                  SET name = ? ,
                      profile_pic = ? ,
                      buyOrders = ? ,
                      sellOrders = ?
                  WHERE id = ?'''
        cur = connection.cursor()
        cur.execute(sql, (name, profile_pic, buyOrders, sellOrders, id_))
        connection.commit()

    @staticmethod
    def create(id_, name, profile_pic, buyOrders, sellOrders):
        connection = eveme.model.get_db()
        connection.execute(
            "INSERT INTO users (id, name, profile_pic, buyOrders, sellOrders) "
            "VALUES (?, ?, ?, ?, ?)",
            (id_, name, profile_pic, buyOrders, sellOrders),
        )
        connection.commit()
