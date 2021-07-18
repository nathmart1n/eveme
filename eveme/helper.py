import eveme


def createHeaders(access_token):
    return {
            "Authorization": "Bearer {}".format(access_token)
           }


def getStructures(user_id):
    connection = eveme.model.get_db()

    structures = connection.execute(
        "SELECT * FROM structureAccess WHERE id = ?", (user_id,)
    ).fetchall()

    return [x['structure_id'] for x in structures]


def insertStructure(user_id, structure_id):
    connection = eveme.model.get_db()
    connection.execute(
        "INSERT OR IGNORE INTO structureAccess (id, structure_id) "
        "VALUES (?, ?)",
        (user_id, structure_id),
    )
    connection.commit()
