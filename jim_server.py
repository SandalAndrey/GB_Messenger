class JIMServer:
    def __init__(self, message):
        self.message=message
        self._actions = {'presence': self.presence, 'msg': self.msg, 'quit': self.quit}

    @log
    def presence(self, data):

        client = self.request

        chat.users[client] = data['user']['account_name']
        app_log.info('{}, {}'.format(client, data))

        msg = str(jim_message.JIMMessage('msg', 'С нами {}!!!'.format(data['user']['account_name'])))

        self._write_to_all(client, msg)

    @log
    def msg(self, data):
        print(data)

        client = self.request

        app_log.info('msg. {}, {}'.format(client, data))

        msg = str(jim_message.JIMMessage('msg', data['message'], fr=data['from']))

        if data['to'] == '*':
            self._write_to_all(client, msg)
        else:
            user = list(chat.users.keys())[list(chat.users.values()).index(data['to'])]
            app_log.info('msg. {}'.format(user))
            if user:
                self._write_to_user(user, msg)

    @log
    def quit(self, data):

        client = self.request
        chat.connections.remove(client)
        msg = str(jim_message.JIMMessage('msg', '{} покинул чат...'.format(data['user']['account_name'])))

        self._write_to_all(client, msg)

        self.request.close()

    def parse_request(self, req):
        try:
            req = json.loads(req)

            action = req['action']
            if not self._actions.get(action):

                raise ValueError(400, 'Нет такой команды - {}'.format(action))

            if action == 'msg':
                if not (req.get('to') and (req['to'] in chat.users.values() or req['to'] == '*')):

                    raise ValueError(404, 'Не найден пользователь {}'.format(req['to']))

            if action == 'presence':
                if req['user']['account_name'] in chat.users.values():

                    raise ValueError(409, 'Уже имеется подключение с указанным логином {}'.format(
                        req['user']['account_name']))

        except ValueError as e:
            print(str(e), e.args[0])
            return {'err_code': e.args[0], 'error': e.args[1], 'request': {}}

        return {'err_code': 200, 'error': 'OK', 'request': req}