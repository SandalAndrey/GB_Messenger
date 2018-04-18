import json
import time

# набор команд взят из методички
ACTIONS = (
    'presence', 'prоbe', 'msg', 'quit', 'authenticate', 'join', 'leave', 'response', 'get_contacts', 'add_contact',
    'del_contact', 'contact', 'search_msg')


class Message:
    def __init__(self, message, action):
        self.action = action
        self._time = time.time()
        self._encoding = 'utf-8'
        self._message = message

    @property
    def message(self):
        return self._message

    @property
    def encoding(self):
        return self._encoding

    @property
    def time(self):
        return self._time

    @property
    def action(self):
        return self._action

    @action.setter
    def action(self, value):
        if value not in ACTIONS:
            raise ValueError("Неверный атрибут {}".format(value))
        else:
            self._action = value

    @message.setter
    def message(self, value):
        self._message = value


class JIMMessage(Message):
    def __init__(self, action, message, to='*', fr='', room=None, user=None):
        super().__init__(message, action)

        self._user = user
        self.fr = fr
        self.to = to
        self.room = room
        # self.__class__.to = CharNumValue(to)
        # self.__class__.room = CharNumValue(room, exc=('#'))

    def __str__(self):
        message = {'action': self.action, 'type': '', 'time': time.time()}

        if self.action == 'msg':
            message['to'] = self.to
            message['from'] = self.fr
            message['room'] = self.room
            message['message'] = self.message

        if self.action == 'join':
            message['room'] = self.room

        if self.action == 'contact':
            message['message'] = self.message
            message['contact'] = self.to

        if self.action == 'search_msg':
            message['message'] = self.message

        if self.action == 'add_contact' or self.action == 'del_contact':
            message['user_id'] = self.to

        account = {'account_name': ''}

        if self._user:
            account = {'account_name': self._user.login, 'status': self._user.status, 'password': self._user.password}
        else:
            account = {'account_name': 'test', 'status': '', 'password': ''}

        message['user'] = account

        return json.dumps(message)

    # @property
    # def to(self):
    #     return self.to
    #
    # @to.setter
    # def to(self, value):
    #     if not (value == '*' or re.fullmatch('[A-ZА-Яa-zа-я_0-9]+', value)):
    #         raise ValueError("Неверный атрибут to: {}".format(value))
    #     else:
    #         self._to = value


class JIMResponse(Message):
    def __init__(self, err_code, message):
        super().__init__(message, 'response')
        self._err_code = err_code

    @property
    def err_code(self):
        return self._err_code

    def __str__(self):
        message = {'response': self.err_code, 'time': time.time()}

        if self.err_code < 400:
            message['alert'] = self.message
        else:
            message['error'] = self.message

        return json.dumps(message)
