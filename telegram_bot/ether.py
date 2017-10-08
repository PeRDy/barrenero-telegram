import peewee
import requests
from telegram import ChatAction, InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.ext import CallbackQueryHandler, CommandHandler

from telegram_bot.persistence import Chat
from telegram_bot.state_machine import StatusState, StatusStateMachine
from telegram_bot.utils import humanize_iso_date


class EtherMixin:
    ether_status_machine = {}

    def ether(self, bot, update):
        """
        Call for Ether miner status and restarting service.
        """
        chat_id = update.message.chat.id
        bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)

        try:
            superuser = Chat.get(id=chat_id)
        except peewee.DoesNotExist:
            self.logger.error('Chat unregistered')
            response_text = 'Configure me first'
            bot.send_message(chat_id, response_text)
        else:
            keyboard = [
                [
                    InlineKeyboardButton("Nanopool", callback_data='[ether_nanopool]')
                ],
            ]
            if superuser:
                keyboard.append(
                    [
                        InlineKeyboardButton("Status", callback_data='[ether_status]'),
                        InlineKeyboardButton("Restart", callback_data='[ether_restart]'),
                    ],
                )
            reply_markup = InlineKeyboardMarkup(keyboard)
            bot.send_message(chat_id, 'Select an option:', reply_markup=reply_markup)

    def ether_nanopool(self, bot, update):
        """
        Query for Nanopool account info.
        """
        query = update.callback_query
        chat_id = query.message.chat_id

        bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)

        try:
            chat = Chat.get(id=chat_id)
            data = self._ether_nanopool_query(chat)
        except peewee.DoesNotExist:
            self.logger.error('Chat unregistered')
            response_text = 'Configure me first'
        else:
            if data:
                response_text = f'*Ether miner*\n' \
                                f' - Balance: `{data["balance"]["confirmed"]} ETH`\n\n' \
                                f'*Hashrate*\n' \
                                f' - Current: `{data["hashrate"]["current"]} MH/s`\n' \
                                f' - 1 hour: `{data["hashrate"]["one_hour"]} MH/s`\n' \
                                f' - 3 hours: `{data["hashrate"]["three_hours"]} MH/s`\n' \
                                f' - 6 hours: `{data["hashrate"]["six_hours"]} MH/s`\n' \
                                f' - 12 hours: `{data["hashrate"]["twelve_hours"]} MH/s`\n' \
                                f' - 24 hours: `{data["hashrate"]["twenty_four_hours"]} MH/s`\n\n' \
                                f'*Last payment*\n' \
                                f' - Date: `{humanize_iso_date(data["last_payment"]["date"])}`\n' \
                                f' - Value: `{data["last_payment"]["value"]} ETH`'
            else:
                response_text = 'Cannot retrieve Nanopool info'
        finally:
            bot.edit_message_text(text=response_text, parse_mode=ParseMode.MARKDOWN, chat_id=query.message.chat_id,
                                  message_id=query.message.message_id)

    def ether_restart(self, bot, update):
        """
        Restart ether systemd service.
        """
        query = update.callback_query
        chat_id = query.message.chat_id

        bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)

        try:
            chat = Chat.get(id=chat_id)
            self._ether_restart_query(chat)
        except peewee.DoesNotExist:
            self.logger.error('Chat unregistered')
            response_text = 'Configure me first'
        else:
            response_text = f'Restarting service.'
        finally:
            bot.edit_message_text(text=response_text, parse_mode=ParseMode.MARKDOWN, chat_id=chat_id,
                                  message_id=query.message.message_id)

    def ether_status(self, bot, update):
        """
        Check Ether miner status.
        """
        query = update.callback_query
        chat_id = query.message.chat_id

        bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)

        try:
            chat = Chat.get(id=chat_id)
            data = self._ether_status_query(chat)
        except peewee.DoesNotExist:
            self.logger.error('Chat unregistered')
            response_text = 'Configure me first'
        else:
            if data:
                response_text = f'*Ether miner*\n' \
                                f' - Status: {data["status"]}\n\n' \
                                f'*Hashrate*\n'
                response_text += '\n'.join([f' - Graphic card #{h["graphic_card"]}: `{h["hashrate"]:.2f} MH/s`'
                                            for h in data['hashrate']])
            else:
                response_text = 'Cannot retrieve Ether miner status'
        finally:
            bot.edit_message_text(text=response_text, parse_mode=ParseMode.MARKDOWN, chat_id=chat_id,
                                  message_id=query.message.message_id)

    def ether_job_status(self, bot, job):
        """
        Check miner status
        """
        # Create new state machines
        new_machines = {c: StatusStateMachine('Ether')
                        for c in Chat.select().where(Chat.superuser == True) if c not in self.ether_status_machine}
        self.ether_status_machine.update(new_machines)

        for chat, status in self.ether_status_machine.items():
            data = self._ether_status_query(chat)

            if data['status'] == StatusState.ACTIVE.value:
                status.start(bot=bot, chat=chat.id)
            else:
                status.stop(bot=bot, chat=chat.id)

    def add_ether_command(self):
        self.dispatcher.add_handler(CommandHandler('ether', self.ether))
        self.dispatcher.add_handler(CallbackQueryHandler(self.ether_nanopool, pattern=r'\[ether_nanopool\]'))
        self.dispatcher.add_handler(CallbackQueryHandler(self.ether_restart, pattern=r'\[ether_restart\]'))
        self.dispatcher.add_handler(CallbackQueryHandler(self.ether_status, pattern=r'\[ether_status\]'))

    def add_ether_jobs(self):
        self.updater.job_queue.run_repeating(self.ether_job_status, 60.0)

    def _ether_nanopool_query(self, chat: 'Chat'):
        url = f'{self._api}/api/v1/ether/nanopool'
        headers = {'Authorization': f'Token {chat.token}'}
        try:
            response = requests.get(url=url, headers=headers)
            response.raise_for_status()
            payload = response.json()
        except requests.HTTPError:
            self.logger.error('Cannot retrieve Nanopool info from Barrenero Ether miner')
            payload = None

        return payload

    def _ether_restart_query(self, chat: 'Chat'):
        url = f'{self._api}/api/v1/restart'
        headers = {'Authorization': f'Token {chat.token}'}
        data = {'name': 'Ether'}
        try:
            response = requests.post(url=url, headers=headers, data=data)
            response.raise_for_status()
            payload = response.json()
        except requests.HTTPError:
            self.logger.error(f'Cannot restart Ether service')
            payload = None

        return payload

    def _ether_status_query(self, chat: 'Chat'):
        url = f'{self._api}/api/v1/ether/status'
        headers = {'Authorization': f'Token {chat.token}'}
        try:
            response = requests.get(url=url, headers=headers)
            response.raise_for_status()
            payload = response.json()
        except requests.HTTPError:
            self.logger.error(f'Cannot retrieve Ether status')
            payload = None

        return payload
