import re


class CharNumValue:
    def __init__(self, value='', exc=()):
        self.value = ''
        self.exc = exc
        self.__set__(self.value, value)

    def __get__(self, obj, obj_type):
        return self.value

    def __set__(self, obj, value):
        if value and not (value == '*' or re.fullmatch('[A-ZА-Яa-zа-я_0-9' + ''.join(self.exc) + ']+', value)):
            raise ValueError("Неверный атрибут: {}".format(value))
        else:
            self.value = value
