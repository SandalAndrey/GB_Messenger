import argparse
from textwrap import dedent

import server_cfg as cfg

parser = argparse.ArgumentParser(description='Клиент чата. Основной процесс...',
                                 formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog=dedent('''        
    Команды работы с чатом:
    --------------------------------        
        help - вывод этого сообщения
        exit - Выход из программы
        
        Любой текст и Enter - Сообщение для всех пользователей
        @UserName message - Приватное сообщение "message" пользователю "UserName"
        
        join #room - Присоединиться к комнате "room" чата
        leave - Покинуть комнату
        
        add_contact UserName - Добавить "UserName" в свой список контактов
        del_contact UserName - Удалить "UserName" из списка контактов
        get_contacts - Получить список контактов
        
        search_msg Текст - Найти и вывести список всех сообщений из БД, содержащих "Текст"
    --------------------------------
        '''))

parser.add_argument('-host', '--addr', required=False, help='ip адрес сервера чата')
parser.add_argument('-port', '--port', required=False, help='порт сервера чата')
parser.add_argument('-username', '--username', required=False, help='имя пользователя (логин)')
parser.add_argument('-password', '--password', required=False,
                    help='пароль пользователя. После установки, вход без пароля станет не возможен...')
parser.add_argument('-message', '--message', required=False, help='сообщение в чат')
parser.add_argument('-autobot', '--autobot', required=False, help='параметр для запуска генерации сообщений в чат')
parser.add_argument('-ui', '--ui', choices=['console', 'colorama', 'graphic', 'kivy'], required=False, help='выбор интерфейса чата')

ars = vars(parser.parse_args())

addr = ars['addr'] if ars['addr'] else cfg.SERVER_HOST
port = int(ars['port']) if ars['port'] else cfg.SERVER_PORT
username = ars['username'] if ars['username'] else ''

password = ars['password'] if ars['password'] else ''
message = ars['message'] if ars['message'] else ''
autobot = ars['autobot'] if ars['autobot'] else ''
ui = ars['ui'] if ars['ui'] else 'graphic'
