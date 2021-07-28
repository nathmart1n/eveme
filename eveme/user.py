from flask_login import UserMixin
from firebase_admin import db, credentials
import eveme
import firebase_admin

# Fetch the service account key JSON file contents
cred = credentials.Certificate('instance/firebaseAccount.json')
# Initialize the app with a service account, granting admin privileges
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://eveme-a9975-default-rtdb.firebaseio.com/'
})

# As an admin, the app has access to read and write all data, regradless of Security Rules
ref = db.reference('users')

# ref = db.reference('https://eveme-a9975-default-rtdb.firebaseio.com/users/', None)


class User(UserMixin):
    def __init__(self, id_, name_, profilePic_, buyOrders_, sellOrders_,
                 accessToken_, structureAccess_):
        self.id = id_
        self.name = name_
        self.profilePic = profilePic_
        self.buyOrders = buyOrders_
        self.sellOrders = sellOrders_
        self.accessToken = accessToken_
        self.structureAccess = structureAccess_

    @staticmethod
    def get(user_id):
        users = ref.get()

        if user_id not in users.keys():
            return None
        selectedUser = users[user_id]
        user = User(
            id_=user_id,
            name_=selectedUser['name'],
            profilePic_=selectedUser['profilePic'],
            buyOrders_=selectedUser['buyOrders'],
            sellOrders_=selectedUser['sellOrders'],
            accessToken_=selectedUser['accessToken'],
            structureAccess_=selectedUser['structureAccess']
        )
        return user

    @staticmethod
    def update(user_info_):
        ref.update(user_info_)

    @staticmethod
    def create(user_info_):
        ref.set(user_info_)
