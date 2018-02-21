#!/usr/bin/env python3.6
import logging
import logging.config
import sys
import time
from functools import wraps

from clinner.command import Type, command
from clinner.run import Main as ClinnerMain

from bot.bot import TelegramBot

DONATE_TEXT = '''
This project is free and open sourced, you can use it, spread the word, contribute to the codebase and help us donating:
* Ether: 0x566d41b925ed1d9f643748d652f4e66593cba9c9
* Bitcoin: 1Jtj2m65DN2UsUzxXhr355x38T6pPGhqiA
* PayPal: barrenerobot@gmail.com
'''


def donate(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)

        print(DONATE_TEXT)

        return result
    return wrapper


class UTCFormatter(logging.Formatter):
    converter = time.gmtime


class Main(ClinnerMain):
    LOGGING = {
        'version': 1,
        'disable_existing_loggers': True,
        'formatters': {
            'value_json': {
                '()': UTCFormatter,
                'format': '{'
                          '"timestamp":"%(asctime)s",'
                          '"value":%(message)s'
                          '}',
                'datefmt': '%Y-%m-%d %H:%M:%S',
            },
            'json': {
                '()': UTCFormatter,
                'format': '{'
                          '"timestamp":"%(asctime)s",'
                          '"level":"%(levelname)s",'
                          '"file":"%(filename)s",'
                          '"line":%(lineno)d,'
                          '"message":"%(message)s"'
                          '}',
                'datefmt': '%Y-%m-%d %H:%M:%S',
            },
            'plain': {
                '()': UTCFormatter,
                'format': '[%(asctime)s] (%(levelname)s:%(filename)s:%(lineno)d) %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S',
            }
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'formatter': 'plain',
                'level': 'INFO',
            },
            'base_file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': 'logs/base.log',
                'formatter': 'plain',
                'level': 'DEBUG',
                'maxBytes': 10 * (2 ** 20),
                'backupCount': 5
            },
            'telegram_file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': 'logs/telegram.log',
                'formatter': 'plain',
                'level': 'DEBUG',
                'maxBytes': 10 * (2 ** 20),
                'backupCount': 5
            },
            'root_file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': 'logs/root.log',
                'formatter': 'plain',
                'level': 'DEBUG',
                'maxBytes': 10 * (2 ** 20),
                'backupCount': 5
            }
        },
        'loggers': {
            'telegram': {
                'handlers': ['console', 'telegram_file'],
                'level': 'INFO',
                'propagate': False
            },
            'bot': {
                'handlers': ['console', 'base_file'],
                'level': 'INFO',
                'propagate': False
            }
        },
        'root': {
            'handlers': ['console', 'root_file'],
            'level': 'INFO',
            'propagate': False
        }
    }

    def __init__(self):
        super().__init__()

        logging.config.dictConfig(self.LOGGING)


@command(command_type=Type.PYTHON,
         args=((('-c', '--config-file'), {'help': 'Config file', 'default': 'config/setup.cfg'}),),
         parser_opts={'help': 'Telegram bot'})
@donate
def start(*args, **kwargs):
    TelegramBot(config=kwargs['config_file']).run()


if __name__ == '__main__':
    sys.exit(Main().run())
