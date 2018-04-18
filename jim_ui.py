import json
import sys
import time

from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QMessageBox
from colorama import Fore, init

import css
import jim_client_db as db
import main_window


class UI:
    """
    Базовый класс ввода-вывода
    """

    def __init__(self, debug=False):
        self.debug = debug

    def start(self, name):
        print('Добро пожаловать в чат, {}'.format(name))

    def read(self, prompt):
        return input(prompt)

    def write(self, message):
        if message:
            print(message)

    def error(self, error, message=''):
        print('error: {}. {}'.format(str(error), message))

    def end(self):
        print('Завершение работы...')

    def help(self):
        print('=' * 77)
        print('\tЛюбой текст и Enter - Сообщение для всех пользователей\n')
        print('\thelp - Это сообщение')
        print('\texit - Выход из программы')
        print('\t@UserName message - Приватное сообщение "message" пользователю "UserName"')
        print('\tjoin #room - Присоединиться к комнате room чата')
        print('\tleave - Покинуть комнату')
        print('\tadd_contact UserName - Добавить UserName в свой список контактов')
        print('\tdel_contact UserName - Удалить UserName из списка контактов')
        print('\tget_contacts - Получить список контактов')
        print()
        print('\tsearch_msg Текст - Найти и вывести список всех сообщений из БД, содержащих текст')
        print('=' * 77)

    def show_contacts(self, contacts):
        if contacts:
            print('Список Ваших контактов:')
            print('-' * 20)
            for contact in contacts:
                print(contact)

    def parse_answer(self, ans):
        if self.debug:
            print(ans)

        try:
            ans = json.loads(ans)
        except json.JSONDecodeError:
            return 444, 'wrong json format\n' + ans

        retstr = ''

        if ans.get('response'):
            if ans['response'] >= 400:
                retstr = '{}. {}'.format(ans['response'], ans['error'])

            if ans['response'] == 202:
                retstr = ans['alert']

        if ans.get('message'):
            retstr = '{}. {}: {}'.format(time.ctime(ans['time']), ans['from'], ans['message'])

        return ans.get('response') if ans.get('response') else 200, retstr


class ConsoleUI(UI):
    """
    todo
    Расширенный консольный класс. + colorama
    """

    def __init__(self, debug=False):
        init(autoreset=True)
        super().__init__(debug)

    def start(self, name):
        print(Fore.LIGHTGREEN_EX + 'Добро пожаловать в чат, {}...'.format(name))
        print(Fore.LIGHTGREEN_EX + 'Сообщение help - помощь по работе с чатом')

    def read(self, prompt):
        return input(prompt)

    def write(self, message):
        if message:
            print(Fore.LIGHTYELLOW_EX + message + Fore.RESET)

    def error(self, error, message=''):
        print(Fore.RED + 'error: {}. {}'.format(str(error), message))

    def end(self):
        print(Fore.LIGHTGREEN_EX + '\nЗавершение работы...')

    def help(self):
        print(Fore.YELLOW + '=' * 77)
        print(Fore.YELLOW + '\tЛюбой текст и Enter - Сообщение для всех пользователей\n')
        print(Fore.YELLOW + '\thelp - Это сообщение')
        print(Fore.YELLOW + '\texit - Выход из программы')
        print(Fore.YELLOW + '\t@UserName message - Приватное сообщение "message" пользователю "UserName"')
        print(Fore.YELLOW + '\tjoin #room - Присоединиться к комнате room чата')
        print(Fore.YELLOW + '\tleave - Покинуть комнату')
        print()
        print(Fore.GREEN + '\tadd_contact UserName - Добавить UserName в свой список контактов')
        print(Fore.GREEN + '\tdel_contact UserName - Удалить UserName из списка контактов')
        print(Fore.GREEN + '\tget_contacts - Получить список контактов')
        print()
        print(Fore.YELLOW + '\tsearch_msg Текст - Найти и вывести список всех сообщений из БД, содержащих текст')

        print(Fore.YELLOW + '=' * 77)

    def show_contacts(self, contacts):
        if contacts:
            print(Fore.LIGHTMAGENTA_EX + '\nСписок Ваших контактов:')
            print(Fore.LIGHTMAGENTA_EX + '-' * 22)
            for contact in contacts:
                if contact.find('(online)') > 0:
                    print(Fore.LIGHTMAGENTA_EX + contact)
                else:
                    print(Fore.MAGENTA + contact)

            print(Fore.LIGHTMAGENTA_EX + '-' * 22)

    def parse_answer(self, ans):
        # print(ans)
        try:
            ans = json.loads(ans)
        except json.JSONDecodeError:
            return 444, 'wrong json format\n' + ans

        retstr = ''

        if ans.get('response'):
            if ans['response'] >= 400:
                retstr = Fore.RED + '{}. {}'.format(ans['response'], ans['error'])

            if ans['response'] == 202:
                retstr = ans['alert']

        if ans.get('contact'):
            return 203, ans['contact'] + ans['message']

        if ans.get('message'):
            color = Fore.LIGHTWHITE_EX
            if not ans['from']:
                color = Fore.LIGHTGREEN_EX
            if ans['message'].find('PRIVATE') > -1:
                color = Fore.LIGHTBLUE_EX

            retstr = color + '{}. {}: {}'.format(time.ctime(ans['time']), ans['from'], ans['message'])

        return ans.get('response') if ans.get('response') else 200, retstr


class GraphicUI(UI):
    """
    Графический интерфейс
    """

    class MyWindow(QtWidgets.QMainWindow):
        def __init__(self, parent=None):
            QtWidgets.QWidget.__init__(self, parent)

            self.ui = main_window.Ui_MainWindow()
            self.ui.setupUi(self)

            ls = ['Общий чат']
            self.ui.contact_list.addItems(ls)
            self.ui.contact_list.setCurrentRow(0)
            self.ui.contact_list.itemSelectionChanged.connect(self.ui.show_List)

            self.ui.okButton.clicked.connect(self.ui.on_pushButtonOK_clicked)

            self.ui.strongButton.clicked.connect(self.ui.on_strongButton_clicked)
            self.ui.italicButton.clicked.connect(self.ui.on_italicButton_clicked)
            self.ui.underButton.clicked.connect(self.ui.on_underButton_clicked)

            self.ui.smile_ab.clicked.connect(self.ui.on_smileAB_clicked)
            self.ui.smile_ac.clicked.connect(self.ui.on_smileAC_clicked)
            self.ui.smile_ai.clicked.connect(self.ui.on_smileAI_clicked)

            # self.ui.lineEdit.returnPressed.connect(self.ui.okButton.click)

    def __init__(self, debug, client):
        self.app = QtWidgets.QApplication(sys.argv)

        self.app.setStyleSheet(css.CSS)
        self.window = self.MyWindow()

        self.window.ui.graphic_ui = self

        self.client = client
        client._qt = self
        self.client._qt = self

        self.photo = None

        super().__init__(debug)

    def show(self):
        self.window.show()
        self.client.run()
        self.app.exec_()

    def parse_answer(self, ans):
        # print(ans)

        try:
            ans = json.loads(ans)
        except json.JSONDecodeError:
            return 444, 'wrong json format\n' + ans

        retstr = ''

        if ans.get('response'):
            if ans['response'] >= 400:
                retstr = '{}. {}'.format(ans['response'], ans['error'])

            if ans['response'] == 202:
                retstr = ans['alert']

        if ans.get('contact'):
            return 203, ans['contact']  # + ans['message']

        if ans.get('message'):
            retstr = '{}. {}: {}'.format(time.ctime(ans['time']), ans['from'], ans['message'])
            retstr = {'from': ans['from'], 'time': ans['time'], 'message': ans['message']}

        return ans.get('response') if ans.get('response') else 200, retstr

    def write(self, message):

        time_ = time.strftime('%Y-%m-%d %H:%M:%S')

        if message:
            if message['message'].startswith('PRIVATE:'):
                pass

            self.window.ui.messageList.addItem('{} {} {}'.format(message['from'], time_, message['message']))

            with db.db_session:
                if message['from']:
                    _ = db.Message(msg_from=message['from'], msg_to=self.client.user.login,
                                   timestamp=time_,
                                   msg=message['message'])

            self.window.ui.messageList.scrollToBottom()

    def start(self, name):
        self.window.setWindowTitle('{} в общем чате'.format(name))

        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)

        msg.setText("Добро пожаловать в чат, " + name)
        # msg.setInformativeText("This is additional information")
        msg.setWindowTitle("Добро пожаловать")
        # msg.setDetailedText("The details are as follows:")
        msg.setStandardButtons(QMessageBox.Ok)

        msg.exec_()

        with db.db_session:
            ava = db.Avatar.get(user=self.client.user.login)
            if ava:
                self.window.ui.photo = ava.photo

    def show_contacts(self, contacts):
        self.window.ui.contact_list.addItems(contacts)
