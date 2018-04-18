import logging
from logging import handlers

format = logging.Formatter('%(asctime)s %(levelname)s %(module)s %(funcName)s %(message)s')

app_log = logging.getLogger('chat_server')
app_log.setLevel(logging.INFO)

handler = logging.handlers.TimedRotatingFileHandler('chat_server.log', when='midnight', interval=1, backupCount=2)
handler.setFormatter(format)
handler.suffix = '%Y-%m-%d-%H-%M'

app_log.addHandler(handler)
