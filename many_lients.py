import os
from subprocess import Popen, CREATE_NEW_CONSOLE

p_list = []  # Список клиентских процессов
while True:
    user = input('Запустить клиентов (s) / Закрыть клиентов (x) / Выйти (q) ')
    if user == 'q':
        break

    elif user == 's':
        cnt = int(input('Количество клиентов: '))
        for k in range(cnt):
            path = os.getcwd()
            path = os.path.join(path, 'client.py')
            p_list.append(Popen('python ' + path + ' -username User' + str(k) + ' -autobot ' + str(cnt),
                                creationflags=CREATE_NEW_CONSOLE))
    elif user == 'x':
        for p in p_list:
            p.kill()
            p_list.clear()
