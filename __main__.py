#!/usr/bin/env python3.6
import logging
import logging.config
import sys
import time

from clinner.command import Type, command
from clinner.run import Main as ClinnerMain

from telegram_bot.bot import TelegramBot


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
            }
        },
        'loggers': {
            'telegram': {
                'handlers': ['console', 'base_file'],
                'level': 'INFO',
                'propagate': False
            }
        }
    }

    def __init__(self):
        super().__init__()

        logging.config.dictConfig(self.LOGGING)


@command(command_type=Type.PYTHON,
         args=((('-c', '--config-file'), {'help': 'Config file', 'default': 'setup.cfg'}),),
         parser_opts={'help': 'Telegram bot'})
def run(*args, **kwargs):
    TelegramBot(config=kwargs['config_file']).run()


if __name__ == '__main__':
    sys.exit(Main().run())
