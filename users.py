import hashlib
import re


def hash(login, password):
    if not password:
        return None

    login = login.encode()
    password = password.encode()

    hsh = hashlib.new('md5')

    hsh.update(login)
    hsh.update(password)

    return hsh.hexdigest()


class User(object):
    def __init__(self, login, email='mail@mail.ru', status='Привет! Я с Вами.'):
        self._login = login
        self._email = email
        self._status = status
        self._password = None

    @property
    def login(self):
        return self._login

    # @login.setter
    # def login(self, value):
    #     if not re.fullmatch('[A-ZА-Яa-zа-я_0-9]+', value):
    #         raise ValueError("Неверное имя пользователя: {}".format(value))
    #     self._login = value

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, value):
        if not isinstance(value, str):
            raise TypeError('Wrong type.')
        self._status = value

    @property
    def email(self):
        return self._email

    @email.setter
    def email(self, value):
        if not re.match('[^@]+@[^@]+\.[^@]+', value):
            raise ValueError('Введен некорректный email')
        self._email = value

    @property
    def password(self):
        return self._password

    @password.setter
    def password(self, value):
        self._password = value

    def set_password(self, password):
        login_bt = self.login.encode('utf-8')

        password_bt = password.encode('utf-8')

        hsh = hashlib.new('md5')

        hsh.update(login_bt)
        hsh.update(password_bt)

        self._password = hsh.hexdigest()

        print('Пароль установлен. Hash: {}'.format(self._password))
