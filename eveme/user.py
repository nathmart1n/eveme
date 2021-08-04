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
ref = db.reference('')
users_ref = ref.child('users')

# ref = db.reference('https://eveme-a9975-default-rtdb.firebaseio.com/users/', None)


class User(UserMixin):
    def __init__(self, id_, accessToken_, authTime_, refreshToken_, name_, profilePic_):
        self.id = id_
        self.accessToken = accessToken_
        self.authTime = authTime_
        self.refreshToken = refreshToken_
        self.profilePic = profilePic_
        self.name = name_

    @staticmethod
    def get(user_id):
        users = users_ref.get()
        if user_id not in users.keys():
            return None
        selectedUser = users[user_id]
        user = User(
            id_=user_id,
            accessToken_=selectedUser['accessToken'],
            authTime_=selectedUser['authTime'],
            refreshToken_=selectedUser['refreshToken'],
            name_=selectedUser['name'],
            profilePic_=selectedUser['profilePic']
        )
        return user

    @staticmethod
    def update(user_info_, user_id_):
        users_ref.child(str(user_id_)).update(user_info_)

    @staticmethod
    def updateAuthToken(newAuthToken, newAuthTime, user_id_):
        users_ref.child(str(user_id_)).update({
            "accessToken": newAuthToken,
            "authTime": newAuthTime
        })

    @staticmethod
    def create(user_info_, user_id_):
        users_ref.child(str(user_id_)).set(user_info_)
