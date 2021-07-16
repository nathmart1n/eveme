from flask_login import UserMixin

import eveme


class User(UserMixin):
    def __init__(self, id_, name_, profile_pic_, buyOrders_, sellOrders_,
                 access_token_):
        self.id = id_
        self.name = name_
        self.profile_pic = profile_pic_
        self.buyOrders = buyOrders_
        self.sellOrders = sellOrders_
        self.access_token = access_token_

    @staticmethod
    def get(user_id):
        connection = eveme.model.get_db()

        user = connection.execute(
            "SELECT * FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        if not user:
            return None
        user = User(
            id_=user['id'],
            name_=user['name'],
            profile_pic_=user['profile_pic'],
            buyOrders_=user['buyOrders'],
            sellOrders_=user['sellOrders'],
            access_token_=user['access_token']
        )
        return user

    @staticmethod
    def update(id_, name_, profile_pic_, buyOrders_, sellOrders_,
               access_token_):
        connection = eveme.model.get_db()
        sql = ''' UPDATE users
                  SET name = ? ,
                      profile_pic = ? ,
                      buyOrders = ? ,
                      sellOrders = ?,
                      access_token = ?
                  WHERE id = ?'''
        cur = connection.cursor()
        cur.execute(sql, (name_, profile_pic_, buyOrders_, sellOrders_,
                          access_token_, id_))
        connection.commit()

    @staticmethod
    def create(id_, name_, profile_pic_, buyOrders_, sellOrders_,
               access_token_):
        connection = eveme.model.get_db()
        connection.execute(
            "INSERT INTO users (id, name, profile_pic, buyOrders, sellOrders, access_token) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (id_, name_, profile_pic_, buyOrders_, sellOrders_, access_token_),
        )
        connection.commit()
