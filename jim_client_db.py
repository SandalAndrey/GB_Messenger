from pony.orm import *
from datetime import datetime

db = Database()


class Message(db.Entity):
    id = PrimaryKey(int, auto=True)
    msg_from = Required(str)
    msg_to = Required(str)
    msg = Required(str)
    timestamp = Required(datetime)

class Avatar(db.Entity):
    user = Required(str)
    photo = Required(bytes)

# db.bind(provider='sqlite', filename=':memory:')
db.bind(provider='sqlite', filename='client.db', create_db=True)

db.generate_mapping(create_tables=True)
