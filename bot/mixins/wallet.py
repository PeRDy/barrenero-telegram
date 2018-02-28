import random
import time
from itertools import takewhile

import peewee
from telegram import ChatAction
from telegram.ext import CommandHandler
from telegram.parsemode import ParseMode

from bot.api import Barrenero
from bot.exceptions import BarreneroRequestException
from bot.models import Chat
from bot.utils import humanize_iso_date


class WalletMixin:
    def wallet(self, bot, update):
        """
        Call for Storj miner status and restarting service.
        """
        chat_id = update.message.chat.id
        bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)

        try:
            chat = Chat.get(id=chat_id)
            api = random.choice(chat.apis)
            data = Barrenero.wallet(api.url, api.token)
        except peewee.DoesNotExist:
            self.logger.error('Chat unregistered')
            response_text = 'Configure me first'
        except BarreneroRequestException as e:
            self.logger.exception(e.message)
            response_text = e.message
        else:
            response_text = f'*Tokens*\n'
            response_text += '\n'.join(
                [f' - {t["name"]}: `{t["balance"]} {t["symbol"]}` ({t.get("balance_usd", "Unknown")} $)'
                 for t in data['tokens'].values()])

            for i, tx in zip(range(1, 4), data['transactions']):
                response_text += f'\n\n*Last transaction #{i}*\n' \
                                 f' - Token: `{tx["token"]["name"]}`\n' \
                                 f' - Hash: `{tx["hash"]}`\n' \
                                 f' - Source: `{tx["source"]}`\n' \
                                 f' - Value: `{tx["value"]} {tx["token"]["symbol"]}`\n' \
                                 f' - Date: `{humanize_iso_date(tx["timestamp"])}`'

        bot.send_message(chat_id, response_text, parse_mode=ParseMode.MARKDOWN)

    def wallet_job_transactions(self, bot, job):
        """
        Check last transaction and notify if there are new payments.
        """
        self.logger.debug('Job: Check transactions')
        for chat in Chat.select():
            api = random.choice(chat.apis)
            data = Barrenero.wallet(api.url, api.token)
            try:
                self.logger.debug('Current transaction: %s', str(chat.last_transaction))
                self.logger.debug('Retrieved transactions: %s', str(data['transactions']))
                first_transaction_hash = data['transactions'][0]['hash']
                if not chat.last_transaction:
                    # If last transaction is unknown, simply update it
                    chat.last_transaction = first_transaction_hash
                else:
                    # Show transactions until last known
                    for tx in takewhile(lambda x: x['hash'] != chat.last_transaction, data['transactions']):
                        text = f'\n\n*Transaction completed*\n' \
                               f' - Token: `{tx["token"]["name"]}`\n' \
                               f' - Value: `{tx["value"]} {tx["token"]["symbol"]}`\n' \
                               f' - Date: `{humanize_iso_date(tx["timestamp"])}`'
                        bot.send_message(text=text, parse_mode=ParseMode.MARKDOWN, chat_id=chat.id)

                    chat.last_transaction = first_transaction_hash
                chat.save()
            except (KeyError, IndexError):
                self.logger.debug('No transactions found for Chat %s', chat.id)
            time.sleep(1)

    def add_wallet_command(self):
        self.updater.dispatcher.add_handler(CommandHandler('wallet', self.wallet))

    def add_wallet_jobs(self):
        self.updater.job_queue.run_repeating(self.wallet_job_transactions, interval=900.0)
