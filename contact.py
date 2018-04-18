class Contact:
    def __init__(self):
        self._count = 0
        self._contact_list = list()

    @property
    def count(self):
        return self._count

    @property
    def contact_list(self):
        return self._contact_list
