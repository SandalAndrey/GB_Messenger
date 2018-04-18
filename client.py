import struct
import threading
import time
from socket import *

import client_args as arg
import jim_message
import jim_ui as ui
import users
from contact import Contact
from descriptor import CharNumValue


class ChatClient:
    __slots__ = ('_addr', '_port', '_user', '_sock', '_contacts', '_qt')

    def __init__(self, addr, port, user=None):
        self._addr = str(addr)
        self._port = int(port)
        self._user = user
        self._sock = None

        self._contacts = None

        self._qt = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        msg = jim_message.JIMMessage('quit', '', user=self.user)
        self.send(str(msg).encode('utf-8'))
        time.sleep(1)
        self.sock.close()

        gui.end()

        if arg.autobot:
            input()

    @property
    def qt(self):
        return self._qt

    @property
    def sock(self):
        return self._sock

    @property
    def user(self):
        return self._user

    @property
    def contacts(self):
        return self._contacts

    def _exception(self, exc, msg):
        err = exc.args[0]
        if err == 10035 or err == 10053:
            time.sleep(0.2)
        elif err == 10061 or err == 10057:
            gui.error('', 'Не удалось установить связь с сервером...')
            exit(1)
        else:
            gui.error(exc, msg)
            exit(1)

    def _connect(self):
        answer = ''
        try:
            self._sock = socket(AF_INET, SOCK_STREAM)
            self._sock.connect((self._addr, self._port))
            # self._sock.setblocking(0)

            if not self.user and self.qt:
                name, ok = self.qt.window.ui.login()
                if not (ok and name):
                    exit()
                self._user = users.User(name)

            msg = jim_message.JIMMessage('presence', '', user=self.user)

            self.send(str(msg).encode('utf-8'))

            answer = self.recv_msg()

        except Exception as e:
            self._exception(e, 'connect')

        return gui.parse_answer(answer.decode('utf-8'))

    def _auth(self):
        """
        Если требуется авторизация - запрашивается пароль и заново формируется и передается запрос presence
        """
        if self.qt:
            password, ok = self.qt.window.ui.password()
            if not (ok and password):
                exit()
        else:
            password = gui.read('Введите пароль:')

        self.user.password = password

        answer = ''
        try:
            msg = jim_message.JIMMessage('presence', '', user=self.user)

            self.send(str(msg).encode('utf-8'))

            answer = self.recv_msg()

        except Exception as e:
            self._exception(e, 'authorization')

        return gui.parse_answer(answer.decode('utf-8'))

    def help(self):
        gui.help()

    def run(self):
        """
        Основной метод класса
        """

        err_code, resp = self._connect()

        # если пароль хранится в БД - требуется авторизация
        if err_code == 401:
            err_code, resp = self._auth()

        if err_code == 200:
            gui.start(self.user.login)  # приветствие

            msg = jim_message.JIMMessage('get_contacts', '')
            self.send(str(msg).encode('utf-8'))

            t = self._start_read()  # запуск потока чтения

            if not self.qt:
                self._start_write()  # запуск передачи сообщений
                t.do_run = False  # остановка потока чтения

        else:
            gui.error(err_code, resp)
            exit(err_code)

    def _send_message(self, user_input, msg_to=''):
        """
        """

        if user_input == 'help':
            self.help()

        if msg_to:
            to = msg_to
            if msg_to != '*':
                user_input = 'PRIVATE:' + user_input
        elif user_input.startswith('@'):
            to = user_input.split()[0]
            user_input = user_input.replace(to, 'PRIVATE:')
            to = to[1:]
        else:
            to = '*'

        try:
            to_ = CharNumValue(to)
        except ValueError:
            gui.error('', 'Введено некорректное имя')
            return

        fr = self.user.login

        msg = jim_message.JIMMessage('msg', user_input, to=to_.value, fr=fr)

        self.send(str(msg).encode('utf-8'))

    def _start_write(self):
        """
        с параметром autobot генерирует случайные сообщения в чат
        """
        if arg.autobot:
            import random
            import string

            k = 1
            while True:

                choice = random.randint(0, 10)

                user_input = '№ {}. '.format(k) + ''.join(random.choices(string.ascii_uppercase + string.digits, k=50))

                msg = jim_message.JIMMessage('msg', user_input, fr=user.login)

                if choice < 1 < k:
                    break
                elif 2 <= choice < 7:
                    gui.write(user_input)
                else:
                    while True:
                        to = 'User' + str(random.randint(0, int(arg.autobot)))
                        if to != self.user.login:
                            break
                    gui.write('@{}: {}'.format(to, user_input))
                    msg.message = 'PRIVATE ' + user_input
                    msg.to = to

                self.send(str(msg).encode('utf-8'))

                time.sleep(0.1)
                k += 1
        else:
            while True:

                user_input = input()
                if not user_input:
                    continue
                if user_input == 'exit':
                    break
                if user_input == 'help':
                    self.help()
                    continue
                to = '*'

                if user_input.startswith('@'):
                    to = user_input.split()[0]
                    user_input = user_input.replace(to, 'PRIVATE:')
                    to = to[1:]

                try:
                    to_ = CharNumValue(to)
                except ValueError:
                    gui.error('', 'Введено некорректное имя')
                    continue
                msg = jim_message.JIMMessage('msg', user_input, to=to_.value, fr=user.login)

                split_input = user_input.split()

                if split_input[0] == 'join':
                    room = split_input[1]
                    if not room.startswith('#'):
                        gui.error(422, 'Имя комнаты должно начинаться с #')
                        continue

                    msg = jim_message.JIMMessage('join', '', room=room)

                if split_input[0] == 'leave':
                    msg = jim_message.JIMMessage('leave', '')

                if split_input[0] == 'get_contacts':
                    msg = jim_message.JIMMessage('get_contacts', '')

                if split_input[0] == 'add_contact' or split_input[0] == 'del_contact':
                    contact = split_input[1]
                    try:
                        contact_ = CharNumValue(contact)
                    except ValueError:
                        gui.error('', 'Введено некорректное имя')
                        continue

                    msg = jim_message.JIMMessage(split_input[0], '', to=contact_.value)

                if split_input[0] == 'search_msg':
                    search_msg = split_input[1]
                    if search_msg:
                        msg = jim_message.JIMMessage(split_input[0], search_msg)

                self.send(str(msg).encode('utf-8'))

    def _start_read(self):
        """
        запуск потока read_thread
        """
        t = threading.Thread(target=self.read_thread)
        t.daemon = True

        t.start()

        return t

    def _get_contacts(self, contact):
        """
        Принимает контакты из потока сообщений. Когда получены все контакты - выводим на экран
        :param contact: Контакт
        """
        self.contacts.contact_list.append(contact)
        self.contacts._count -= 1

        if not self.contacts.count:
            gui.show_contacts(self.contacts.contact_list)

    def read_thread(self):
        t = threading.currentThread()
        reply = ''

        # остановка задачи
        while getattr(t, 'do_run', True):
            try:
                reply = self.recv_msg()
                if reply:
                    err_code, response = gui.parse_answer(reply.decode('utf-8'))
                    if err_code and err_code == 202:
                        if not self.contacts:
                            self._contacts = Contact()
                        else:
                            self._contacts._contact_list = list()
                        self.contacts._count = int(response)

                    elif err_code and err_code == 203:
                        self._get_contacts(response)

                    elif err_code and err_code != 200:
                        gui.error(err_code, response)
                    else:
                        # вывод сообщения пользователю
                        gui.write(response)

            except error as e:
                self._exception(e, reply)

    def recv_msg(self):
        """
        получаем 4 байта - длину сообщения и загружаем все сообщение
        """
        raw_msglen = self.recvall(4)

        if not raw_msglen:
            return None
        msglen = struct.unpack('>I', raw_msglen)[0]

        return self.recvall(msglen)

    def recvall(self, n):
        """
        читаем данные из потока
        :param n: количество байт
        :return:
        """
        data = b''

        while len(data) < n:
            packet = self.sock.recv(n - len(data))
            if not packet:
                return None
            data += packet

        return data

    def send(self, msg):
        """
        передача сообщения серверу
        :param msg: сообщение
        """
        try:
            self.sock.send(msg + b'\n')

        except error as e:
            self._exception(e, msg)


if __name__ == '__main__':

    gui = None
    user = None
    username = None

    # Закомментированные ниже 2 строки - используется граф. интерфейс.
    if arg.ui == 'console':
        gui = ui.UI(False)
    elif arg.ui == 'colorama':
        gui = ui.ConsoleUI(True)

    if arg.username:
        username = arg.username
    else:
        if gui:
            username = gui.read('Введите Ваше имя: ')

    if username:
        try:
            username_ = CharNumValue(username)
        except ValueError:
            print('Введен некорректный логин')
        else:
            user = users.User(username_.value)
            if arg.password:
                user.password = arg.password

    with ChatClient(arg.addr, arg.port, user=user) as client:
        if gui:
            client.run()
        else:
            gui = ui.GraphicUI(False, client)
            gui.show()
