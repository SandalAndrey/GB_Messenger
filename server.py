import inspect
import json
import struct
import time
from collections import namedtuple
import asyncio

import jim_db as db
import jim_message
import server_cfg as cfg
from log_config import *
from users import hash

Client = namedtuple('Client', 'reader writer')


def log(fn):
    def wrapped(*args, **kwargs):
        msg = 'Функция {} вызвана из функции {}'.format(fn.__name__, inspect.stack()[1][3])
        app_log.info(msg)

        fn(*args, **kwargs)

    return wrapped


class Server:
    def __init__(self):
        """
        _actions - список соответствия команд чата методам класса
        """
        self._actions = {'presence': self.presence, 'msg': self.msg, 'quit': self.quit, 'join': self.join,
                         'leave': self.leave, 'get_contacts': self.get_contacts, 'add_contact': self.add_contact,
                         'del_contact': self.del_contact, 'search_msg': self.search_msg}

        # self._connections = []
        self._users = {}
        self._rooms = {}
        self.clients = {}

        self.server = None

        self.loop = asyncio.get_event_loop()

    @asyncio.coroutine
    def run_server(self):
        try:
            self.server = yield from asyncio.start_server(self.client_connected, cfg.SERVER_HOST, cfg.SERVER_PORT)
            print('Сервер запущен {}:{}'.format(cfg.SERVER_HOST, cfg.SERVER_PORT))
        except OSError as e:
            print('Ошибка при запуске сервера {}'.format(e))
            self.loop.stop()

    @log
    def presence(self, data, peer):
        """
        Регистрация клиента в чате
        :param data:  - presence сообщение
        """

        self.users[self.clients[peer]] = data['user']['account_name']  # соответствие сокета экземпляру класса User

        app_log.info('{}, {}'.format(peer, data))

        msg = str(jim_message.JIMMessage('msg', 'С нами {}!!!'.format(data['user']['account_name'])))

        self._write_to_all(peer, msg)

        with db.db_session:
            if not db.Client.get(login=data['user']['account_name']):
                new_cli = db.Client(login=data['user']['account_name'])
                if data['user'].get('password'):
                    new_cli.password = data['user']['password']
            else:
                new_cli = db.Client.get(login=data['user']['account_name'])

            _ = db.ClientHistory(client=new_cli, timestamp=time.strftime('%Y-%m-%d %H:%M:%S'),
                                 ipaddress=peer[0])

    @log
    def msg(self, data, peer):
        """
        Обработка сообщения от клиента. Передача всем (*) или конкретному юзеру
        :param data: сообщение
        """

        app_log.info('{}, {}'.format(peer, data))

        msg = str(jim_message.JIMMessage('msg', data['message'], fr=data['from']))

        if data['to'] == '*':
            self._write_to_all(peer, msg)
        else:
            # определение сокета по имени пользователя
            try:
                user = list(self.users.keys())[list(self.users.values()).index(data['to'])]
                if user:
                    self._write_to_user(user, msg)
            except ValueError:
                pass

        with db.db_session:
            if self.users.get(self.clients[peer]):
                owner = db.Client.get(login=self.users[self.clients[peer]])
                _ = db.MessageHistory(client=owner, message=data['message'], to=data['to'],
                                      timestamp=time.strftime('%Y-%m-%d %H:%M:%S'))

    @log
    def join(self, data, peer):
        """
        Присоединение к "комнате" чата
        :param data:
        """
        # todo реализовать присоединение

        app_log.info('{}, {}'.format(peer, data))

        self.rooms[peer] = data['room']

        msg = str(jim_message.JIMMessage('msg', 'Добро пожаловать в комнату {}'.format(data['room'])))

        self._write_to_user(self.clients[peer], msg)

    @log
    def leave(self, data, peer):
        """
        Выход из комнаты
        :param data:
        """

        app_log.info('{}, {}'.format(peer, data))

        if self.rooms.get(peer):
            msg = str(jim_message.JIMMessage('msg', 'Вы покинули комнату {}'.format(self.rooms[peer])))

            self.rooms[peer] = ''

            self._write_to_user(self.clients[peer], msg)

    @log
    def search_msg(self, data, peer):

        app_log.info('{}, {}'.format(peer, data))

        with db.db_session:
            messages = db.select(msg for msg in db.MessageHistory if data['message'] in msg.message and (
                    msg.to == '*' or msg.to == self.users[self.clients[peer]]))[:]

            for message in messages:
                msg = str(
                    jim_message.JIMMessage('msg', '{}: {} - {}'.format(message.timestamp, message.to, message.message)))

                self._write_to_user(self.clients[peer], msg)

    @log
    def get_contacts(self, data, peer):
        """
        Получает список контактов и передает клиенту. Сначала количество, затем контакты. (как в методичке)
        Передается статус (онлайн контакт или оффлайн...)
        """
        app_log.info('{}, {}'.format(peer, data))

        with db.db_session:
            contacts = db.select(
                cli for c in db.Contact for o in c.owner for cli in db.Client if cli.id == c.contact and
                o.login == self.users[self.clients[peer]])[:]
            if contacts:
                msg = str(jim_message.JIMResponse(202, str(len(contacts))))
                self._write_to_user(self.clients[peer], msg)

                for contact in contacts:
                    if contact.login in self.users.values():
                        online = ' (online)'
                    else:
                        online = ' (offline)'
                    msg = str(jim_message.JIMMessage('contact', '', to=contact.login))
                    self._write_to_user(self.clients[peer], msg)

    @log
    def add_contact(self, data, peer):
        """
        Добавляет контакт
        """

        app_log.info('{}, {}'.format(peer, data))

        with db.db_session:
            owner = db.Client.get(login=self.users[self.clients[peer]])
            contact = db.Client.get(login=data['user_id'])

            if contact:
                if not (db.Contact.get(owner=owner, contact=contact.id) or owner == contact):
                    _ = db.Contact(owner=owner, contact=contact.id)
                    msg = str(
                        jim_message.JIMMessage('msg', '{} добавлен в Ваш список контактов'.format(data['user_id'])))
                else:
                    msg = ''
            else:
                msg = str(jim_message.JIMResponse(404, 'Не найден клиент {}'.format(data['user_id'])))

            if msg:
                self._write_to_user(self.clients[peer], msg)

    @log
    def del_contact(self, data, peer):
        """
        Удаление контакта
        """

        app_log.info('{}, {}'.format(peer, data))

        with db.db_session:
            owner = db.Client.get(login=self.users[self.clients[peer]])
            contact = db.Client.get(login=data['user_id'])

            if contact:
                db.delete(c for c in db.Contact if c.owner == owner and c.contact == contact.id)
                msg = str(jim_message.JIMMessage('msg', '{} удален из Вашего списка контактов'.format(data['user_id'])))
            else:
                msg = str(jim_message.JIMResponse(404, 'Не найден клиент {}'.format(data['user_id'])))

            self._write_to_user(self.clients[peer], msg)

    @log
    def quit(self, data, peer):
        """
        Сообщение о выходе клиента из чата
        :param data:
        """
        # self.connections.remove(client)

        self.users[self.clients[peer]] = ''

        msg = str(jim_message.JIMMessage('msg', '{} покинул чат...'.format(data['user']['account_name'])))

        self._write_to_all(peer, msg)

        del self.clients[peer]

        app_log.info('{}, {}'.format(peer, data))

    def _auth(self, login, password):
        """
        первоначальное присваивание пароля или авторизация при необходимости
        :param login:
        :param password:
        """
        pass_md5 = hash(login, password)

        with db.db_session:
            client = db.Client.get(login=login)

            if client:
                if client.password:
                    if client.password == pass_md5:
                        app_log.info('{} - успешная авторизация'.format(login))
                        return True
                    else:
                        app_log.error('неверный пароль {} - для пользователя {}'.format(password, login))
                        return False
                else:
                    if password:
                        client.password = pass_md5
                        app_log.info('{} - задан пароль {}'.format(login, password))
                    else:
                        app_log.info('{} - без авторизации'.format(login))
                    return True
            else:
                app_log.info('{} - без авторизации'.format(login))
                return True

    def parse_request(self, req, peer):
        """
        разбор сообщения
        :param req: запрос
        :return: возвращает коды ошибок и JSON запрос
        """
        try:
            req = json.loads(req)

            action = req['action']

            if not self._actions.get(action):
                raise ValueError(421, 'Нет такой команды - {}'.format(action))

            if action == 'msg':
                if not (req.get('to') and (req['to'] in self.users.values() or req['to'] == '*')):
                    raise ValueError(404, 'Не найден пользователь {}'.format(req['to']))

            if action == 'join':
                if self.rooms.get(peer):
                    raise ValueError(422, 'Вы уже находитесь в комнате {}'.format(self.rooms[peer]))

            if action == 'presence':
                if req['user']['account_name'] in self.users.values():
                    raise ValueError(409, 'Уже имеется подключение с указанным логином {}'.format(
                        req['user']['account_name']))

                password = req['user'].get('password', '')
                if not self._auth(req['user']['account_name'], password):
                    # если пароль передан в запросе, но не совпадает с сохраненным в БД
                    if password:
                        raise ValueError(402, 'Неверный пароль для пользователя {}'.format(
                            req['user']['account_name']))
                    # если пароль хранится в БД, но не передан в запросе
                    else:
                        raise ValueError(401, 'Требуется авторизация пользователя {}'.format(
                            req['user']['account_name']))


        except ValueError as e:
            return {'err_code': e.args[0], 'error': e.args[1], 'request': {}}

        return {'err_code': 200, 'error': 'OK', 'request': req}

    @log
    def _write_to_all(self, from_, msg):
        """
        broadcast
        :param from_: сокет отправитель
        :param msg: сообщение
        """
        # получаем список активных сокетов исключая отправителя

        room_from = self.rooms.get(from_, '')

        try:
            for client_peername, client in self.clients.items():
                if room_from == self.rooms.get(client_peername, '') and client_peername != from_:
                    self._write_to_user(client, msg)

        except Exception as e:
            print(str(e))
            raise

    @log
    def _write_to_user(self, client, msg):
        """
        Передача сообщения в конкретный сокет
        :param client: сокет
        :param msg: сообщение
        """
        try:
            # передаем длину сообщения в структуре и само сообщение
            client.writer.write(struct.pack('>I', len(msg)) + msg.encode('utf-8'))

        except (ConnectionResetError, OSError, ConnectionAbortedError):
            self._client_exception(client)

    def _client_exception(self, cli):

        if cli.fileno() > 0:
            app_log.exception('client {} {} disconnected.'.format(cli.fileno(), cli.getpeername()))
            cli.close()

        if cli in self.users:
            msg = str(jim_message.JIMMessage('msg', '{} покинул чат...'.format(self.users[cli])))
            self.users.pop(cli)
            self._write_to_all(None, msg)

        if cli in self.connections:
            self.connections.remove(cli)

    @asyncio.coroutine
    def client_connected(self, reader, writer):
        peername = writer.transport.get_extra_info('peername')

        new_client = Client(reader, writer)
        self.clients[peername] = new_client
        print('Подключение клиента: {}'.format(peername))
        while not reader.at_eof():
            try:
                msg = yield from reader.readline()
                if msg:
                    cmd = self.parse_request(msg, peername)

                    msg = str(jim_message.JIMResponse(cmd['err_code'], cmd['error']))
                    try:
                        new_client.writer.write(struct.pack('>I', len(msg)) + msg.encode('utf-8'))
                    except ConnectionResetError as e:
                        print('ConnectionResetError: {}'.format(e))
                        continue
                    if cmd['err_code'] == 200:
                        req = cmd['request']
                        # вызов метода по имени команды
                        self._actions[req['action']](req, peername)

            except Exception as e:
                print('ERROR: {}'.format(e))
                # del self.clients[peername]
                return

    def close(self):
        self.close_clients()
        self.loop.stop()

    def close_clients(self):
        print('Sending EndOfFile to all clients to close them.')
        for peername, client in self.clients.items():
            client.writer.write_eof()

    # @property
    # def connections(self):
    #     return self._connections

    @property
    def users(self):
        return self._users

    @property
    def rooms(self):
        return self._rooms


if __name__ == "__main__":

    loop = asyncio.get_event_loop()
    mainserver = Server()
    asyncio.async(mainserver.run_server())
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        print('Сервер остановлен.')
        mainserver.close()
    finally:
        loop.close()
