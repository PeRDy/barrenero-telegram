import time
from itertools import takewhile

import peewee
import requests
from telegram import ChatAction
from telegram.ext import CommandHandler
from telegram.parsemode import ParseMode

from telegram_bot.persistence import Chat
from telegram_bot.utils import humanize_iso_date


class WalletMixin:
    def wallet(self, bot, update):
        """
        Call for Storj miner status and restarting service.
        """
        chat_id = update.message.chat.id
        bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)

        try:
            chat = Chat.get(id=chat_id)
            data = self._wallet_query(chat)
        except peewee.DoesNotExist:
            self.logger.error(f'Chat unregistered')
            response_text = 'Configure me first'
        else:
            if data:
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
            else:
                response_text = "Cannot retrieve wallet info"
        finally:
            bot.send_message(chat_id, response_text, parse_mode=ParseMode.MARKDOWN)

    def wallet_job_transactions(self, bot, job):
        """
        Check last transaction and notify if there are new payments.
        """
        # Create new state machines
        for chat in Chat.select():
            data = self._wallet_query(chat)
            try:
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
        self.dispatcher.add_handler(CommandHandler('wallet', self.wallet))

    def add_wallet_jobs(self):
        self.updater.job_queue.run_repeating(self.wallet_job_transactions, 900.0)

    def _wallet_query(self, chat: 'Chat'):
        try:
            url = f'{self._api}/api/v1/wallet'
            headers = {'Authorization': f'Token {chat.token}'}
            response = requests.get(url=url, headers=headers)
            response.raise_for_status()
            payload = response.json()
        except requests.HTTPError:
            self.logger.error('Cannot retrieve wallet info')
            payload = None

        return payload
