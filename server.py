import inspect
import json
import struct
import time
from socketserver import StreamRequestHandler, ThreadingTCPServer

import select as sel

import jim_db as db
import jim_message
import server_cfg as cfg
from log_config import *
from users import hash


def log(fn):
    def wrapped(*args, **kwargs):
        msg = 'Функция {} вызвана из функции {}'.format(fn.__name__, inspect.stack()[1][3])
        app_log.info(msg)

        fn(*args, **kwargs)

    return wrapped


class ChatHandler(StreamRequestHandler):
    def __init__(self, request, client_address, server):
        """
        _actions - список соответствия команд чата методам класса
        """
        self._actions = {'presence': self.presence, 'msg': self.msg, 'quit': self.quit, 'join': self.join,
                         'leave': self.leave, 'get_contacts': self.get_contacts, 'add_contact': self.add_contact,
                         'del_contact': self.del_contact, 'search_msg': self.search_msg}

        StreamRequestHandler.__init__(self, request, client_address, server)

    @log
    def presence(self, data):
        """
        Регистрация клиента в чате
        :param data:  - presence сообщение
        """
        client = self.request

        chat.users[client] = data['user']['account_name']  # соответствие сокета экземпляру класса User

        app_log.info('{}, {}'.format(client, data))

        msg = str(jim_message.JIMMessage('msg', 'С нами {}!!!'.format(data['user']['account_name'])))

        self._write_to_all(client, msg)

        with db.db_session:
            if not db.Client.get(login=data['user']['account_name']):
                new_cli = db.Client(login=data['user']['account_name'])
                if data['user'].get('password'):
                    new_cli.password = data['user']['password']
            else:
                new_cli = db.Client.get(login=data['user']['account_name'])

            _ = db.ClientHistory(client=new_cli, timestamp=time.strftime('%Y-%m-%d %H:%M:%S'),
                                 ipaddress=self.client_address[0])

    @log
    def msg(self, data):
        """
        Обработка сообщения от клиента. Передача всем (*) или конкретному юзеру
        :param data: сообщение
        """
        client = self.request

        app_log.info('{}, {}'.format(client, data))

        msg = str(jim_message.JIMMessage('msg', data['message'], fr=data['from']))

        if data['to'] == '*':
            self._write_to_all(client, msg)
        else:
            # определение сокета по имени пользователя
            try:
                user = list(chat.users.keys())[list(chat.users.values()).index(data['to'])]
                if user:
                    self._write_to_user(user, msg)
            except ValueError:
                pass

        with db.db_session:
            if chat.users.get(client):
                owner = db.Client.get(login=chat.users[client])
                _ = db.MessageHistory(client=owner, message=data['message'], to=data['to'],
                                      timestamp=time.strftime('%Y-%m-%d %H:%M:%S'))

    @log
    def join(self, data):
        """
        Присоединение к "комнате" чата
        :param data:
        """
        # todo реализовать присоединение
        client = self.request

        app_log.info('{}, {}'.format(client, data))

        chat.rooms[client] = data['room']

        msg = str(jim_message.JIMMessage('msg', 'Добро пожаловать в комнату {}'.format(data['room'])))

        self._write_to_user(client, msg)

    @log
    def leave(self, data):
        """
        Выход из комнаты
        :param data:
        """

        client = self.request

        app_log.info('{}, {}'.format(client, data))

        if chat.rooms.get(client):
            msg = str(jim_message.JIMMessage('msg', 'Вы покинули комнату {}'.format(chat.rooms[client])))

            chat.rooms[client] = ''

            self._write_to_user(client, msg)

    @log
    def get_contacts(self, data):
        """
        Получает список контактов и передает клиенту. Сначала количество, затем контакты. (как в методичке)
        Передается статус (онлайн контакт или оффлайн...)
        """

        client = self.request

        app_log.info('{}, {}'.format(client, data))

        with db.db_session:
            contacts = db.select(
                cli for c in db.Contact for o in c.owner for cli in db.Client if cli.id == c.contact and
                o.login == chat.users[client])[:]
            if contacts:
                msg = str(jim_message.JIMResponse(202, str(len(contacts))))
                self._write_to_user(client, msg)

                for contact in contacts:
                    if contact.login in chat.users.values():
                        online = ' (online)'
                    else:
                        online = ' (offline)'
                    msg = str(jim_message.JIMMessage('contact', online, to=contact.login))
                    self._write_to_user(client, msg)

    @log
    def add_contact(self, data):
        """
        Добавляет контакт
        """

        app_log.info('{}, {}'.format(self.request, data))

        with db.db_session:
            owner = db.Client.get(login=chat.users[self.request])
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
                self._write_to_user(self.request, msg)

    @log
    def del_contact(self, data):
        """
        Удаление контакта
        """

        app_log.info('{}, {}'.format(self.request, data))

        with db.db_session:
            owner = db.Client.get(login=chat.users[self.request])
            contact = db.Client.get(login=data['user_id'])

            if contact:
                db.delete(c for c in db.Contact if c.owner == owner and c.contact == contact.id)
                msg = str(jim_message.JIMMessage('msg', '{} удален из Вашего списка контактов'.format(data['user_id'])))
            else:
                msg = str(jim_message.JIMResponse(404, 'Не найден клиент {}'.format(data['user_id'])))

            self._write_to_user(self.request, msg)

    @log
    def search_msg(self, data):

        app_log.info('{}, {}'.format(self.request, data))

        with db.db_session:
            messages = db.select(msg for msg in db.MessageHistory if data['message'] in msg.message and (
                    msg.to == '*' or msg.to == chat.users[self.request]))[:]

            for message in messages:
                msg = str(
                    jim_message.JIMMessage('msg', '{}: {} - {}'.format(message.timestamp, message.to, message.message)))

                self._write_to_user(self.request, msg)

    @log
    def quit(self, data):
        """
        Сообщение о выходе клиента из чата
        :param data:
        """
        client = self.request

        chat.connections.remove(client)
        chat.users[client] = ''

        msg = str(jim_message.JIMMessage('msg', '{} покинул чат...'.format(data['user']['account_name'])))

        self._write_to_all(client, msg)

        self.request.close()

        app_log.info('{}, {}'.format(self.request, data))

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

    def parse_request(self, req):
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
                if not (req.get('to') and (req['to'] in chat.users.values() or req['to'] == '*')):
                    raise ValueError(404, 'Не найден пользователь {}'.format(req['to']))

            if action == 'join':
                if chat.rooms.get(self.request):
                    raise ValueError(422, 'Вы уже находитесь в комнате {}'.format(chat.rooms[self.request]))

            if action == 'presence':
                if req['user']['account_name'] in chat.users.values():
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

        room_from = chat.rooms.get(from_, '')

        active = list(x for x in chat.connections if x.fileno() > -1 and x != from_)
        if active:
            try:
                _, write, _ = sel.select([], active, [])
                for client in write:
                    if room_from == chat.rooms.get(client, ''):
                        self._write_to_user(client, msg)

            except Exception as e:
                print(active)
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
            client.send(struct.pack('>I', len(msg)) + msg.encode('utf-8'))

        except (ConnectionResetError, OSError, ConnectionAbortedError):
            self._client_exception(client)

    def _client_exception(self, cli):

        if cli.fileno() > 0:
            app_log.exception('client {} {} disconnected.'.format(cli.fileno(), cli.getpeername()))
            cli.close()

        if cli in chat.users:
            msg = str(jim_message.JIMMessage('msg', '{} покинул чат...'.format(chat.users[cli])))
            chat.users.pop(cli)
            self._write_to_all(None, msg)

        if cli in chat.connections:
            chat.connections.remove(cli)

    def handle(self):
        while True:
            try:
                command = self.rfile.readline().decode('utf-8')
            except (ConnectionResetError, ConnectionAbortedError):
                time.sleep(0.1)
                continue
            else:
                if self.request not in chat.connections:
                    chat.connections.append(self.request)
            if not command:
                break

            request = self.parse_request(command)

            msg = str(jim_message.JIMResponse(request['err_code'], request['error']))

            try:
                self.wfile.write(struct.pack('>I', len(msg)) + msg.encode('utf-8'))
            except ConnectionResetError as e:
                # self._client_exception(self.request)
                continue

            if request['err_code'] == 200:
                req = request['request']

                # вызов метода по имени команды
                self._actions[req['action']](req)


class ChatServer(ThreadingTCPServer):
    def __init__(self, server_address, handler_class):
        self._connections = []
        self._users = {}
        self._rooms = {}

        ThreadingTCPServer.__init__(self, server_address, handler_class)

    allow_reuse_address = True

    @property
    def connections(self):
        return self._connections

    @property
    def users(self):
        return self._users

    @property
    def rooms(self):
        return self._rooms


if __name__ == "__main__":
    chat = ChatServer((cfg.SERVER_HOST, cfg.SERVER_PORT), ChatHandler)
    print('Сервер стартовал...')
    chat.serve_forever()
