import _mysql
from datetime import datetime

from pony.orm import *

import server_cfg as cfg

db = Database()


class Client(db.Entity):
    id = PrimaryKey(int, auto=True)
    login = Required(str)
    email = Optional(str)
    status = Optional(str)
    password = Optional(str)
    client_historys = Set('ClientHistory')
    contacts = Set('Contact')
    message_hystorys = Set('MessageHistory')


class ClientHistory(db.Entity):
    id = PrimaryKey(int, auto=True)
    client = Required(Client)
    timestamp = Required(datetime)
    ipaddress = Required(str)


class Contact(db.Entity):
    id = PrimaryKey(int, auto=True)
    owner = Required(Client)
    contact = Required(int)


class MessageHistory(db.Entity):
    id = PrimaryKey(int, auto=True)
    client = Required(Client)
    message = Required(str)
    to = Required(str)
    room = Optional(str)
    timestamp = Required(datetime)


try:
    db.bind(provider='mysql', host=cfg.MYSQL_HOST, user=cfg.MYSQL_LOGIN, passwd=cfg.MYSQL_PASSWORD, db=cfg.MYSQL_DB,
            charset='utf8')
except OperationalError as e:
    conn = _mysql.connect(cfg.MYSQL_HOST, cfg.MYSQL_LOGIN, cfg.MYSQL_PASSWORD)
    conn.query('create database {} collate utf8_general_ci'.format(cfg.MYSQL_DB))
    conn.close()

    db.bind(provider='mysql', host=cfg.MYSQL_HOST, user=cfg.MYSQL_LOGIN, passwd=cfg.MYSQL_PASSWORD, db=cfg.MYSQL_DB,
            charset='utf8')

db.generate_mapping(create_tables=True)
