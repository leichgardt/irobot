import logging

f_format = logging.Formatter('[%(asctime)s] %(levelname)s - in %(filename)s: %(funcName)s(%(lineno)d): %(message)s')
s_format = logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s')
logfile = '/var/log/iron/mega_bot.log'


def __init_logger(name):
    s_handler = logging.StreamHandler()
    s_handler.setLevel(logging.INFO)
    s_handler.setFormatter(s_format)
    f_handler = logging.FileHandler(logfile)
    f_handler.setLevel(logging.WARNING)
    f_handler.setFormatter(f_format)

    logger = logging.getLogger(name)
    logger.addHandler(s_handler)
    logger.addHandler(f_handler)
    logger.setLevel(logging.INFO)
    return logger


logger = __init_logger('iro-mega-bot')
