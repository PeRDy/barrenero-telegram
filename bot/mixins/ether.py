import peewee
from telegram import ChatAction, InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.ext import CallbackQueryHandler, CommandHandler

from bot.api import Barrenero
from bot.exceptions import BarreneroRequestException
from bot.models import API, Chat
from bot.state_machine import StatusStateMachine
from bot.utils import humanize_iso_date


class EtherMixin:
    ether_status_machine = {}

    def ether(self, bot, update):
        """
        Call for Ether miner status and restarting service.
        """
        chat_id = update.message.chat.id
        bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)

        try:
            Chat.get(id=chat_id)
        except peewee.DoesNotExist:
            self.logger.error('Chat unregistered')
            response_text = 'Configure me first'
            bot.send_message(chat_id, response_text)
        else:
            keyboard = [
                [
                    InlineKeyboardButton("Status", callback_data='[ether_status]'),
                    InlineKeyboardButton("Nanopool", callback_data='[ether_nanopool]')
                ],
                [
                    InlineKeyboardButton("Restart", callback_data='[ether_restart]'),
                ],
            ]
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
            data = Barrenero.ether(chat.apis[0].url, chat.apis[0].token)
        except peewee.DoesNotExist:
            self.logger.error('Chat unregistered')
            response_text = 'Configure me first'
        except BarreneroRequestException as e:
            self.logger.exception(e.message)
            response_text = e.message
        else:
            try:
                response_text = f'*Ether miner*\n' \
                                f' - Balance: `{data["nanopool"]["balance"]["confirmed"]} ETH`\n\n' \
                                f'*Hashrate*\n' \
                                f' - Current: `{data["nanopool"]["hashrate"]["current"]} MH/s`\n' \
                                f' - 1 hour: `{data["nanopool"]["hashrate"]["one_hour"]} MH/s`\n' \
                                f' - 3 hours: `{data["nanopool"]["hashrate"]["three_hours"]} MH/s`\n' \
                                f' - 6 hours: `{data["nanopool"]["hashrate"]["six_hours"]} MH/s`\n' \
                                f' - 12 hours: `{data["nanopool"]["hashrate"]["twelve_hours"]} MH/s`\n' \
                                f' - 24 hours: `{data["nanopool"]["hashrate"]["twenty_four_hours"]} MH/s`\n\n' \
                                f'*Last payment*\n' \
                                f' - Date: `{humanize_iso_date(data["nanopool"]["last_payment"]["date"])}`\n' \
                                f' - Value: `{data["nanopool"]["last_payment"]["value"]} ETH`\n\n' \
                                f'*Workers*\n' + \
                                '\n'.join(f' - {w}: `{v} MH/s`' for w, v in data['nanopool']['workers'].items())
            except (KeyError, TypeError):
                response_text = 'Cannot retrieve Nanopool info'
                self.logger.exception('Barrenero API wrong response for Nanopool info: %s', str(data))

        bot.edit_message_text(text=response_text, parse_mode=ParseMode.MARKDOWN, chat_id=query.message.chat_id,
                              message_id=query.message.message_id)

    def ether_miner_choice(self, bot, update, groups):
        """
        Call for Ether miner status and restarting service.
        """
        query = update.callback_query
        action = groups[0]
        chat_id = query.message.chat_id
        bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
        try:
            chat = Chat.get(id=chat_id)
        except peewee.DoesNotExist:
            chat = False

        if chat:
            buttons = [InlineKeyboardButton(api.name, callback_data=f'[ether_{action}][{api.id}]')
                       for api in chat.apis if api.superuser]
            keyboard = [buttons[i:max(len(buttons), i + 4)] for i in range(0, len(buttons), 4)]
            reply_markup = InlineKeyboardMarkup(keyboard)
        else:
            reply_markup = None

        if reply_markup:
            bot.edit_message_text(text='Select miner:', reply_markup=reply_markup, chat_id=chat_id,
                                  message_id=query.message.message_id)
        else:
            bot.edit_message_text(text='No options available', chat_id=chat_id, message_id=query.message.message_id)

    def ether_restart(self, bot, update, groups):
        """
        Restart ether systemd service.
        """
        query = update.callback_query
        api_id = groups[0]
        chat_id = query.message.chat_id

        bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)

        try:
            api = API.get(id=api_id)
            Barrenero.restart(api.url, api.token, 'Ether')

        except peewee.DoesNotExist:
            self.logger.error('Chat unregistered')
            response_text = 'Configure me first'
            bot.edit_message_text(text=response_text, parse_mode=ParseMode.MARKDOWN, chat_id=chat_id,
                                  message_id=query.message.message_id)
        else:
            response_text = f'Restarting service `{api.name}`.'
            bot.edit_message_text(text=response_text, parse_mode=ParseMode.MARKDOWN, chat_id=chat_id,
                                  message_id=query.message.message_id)

    def ether_status(self, bot, update, groups):
        """
        Check Ether miner status.
        """
        query = update.callback_query
        api_id = groups[0]
        chat_id = query.message.chat_id

        bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)

        try:
            api = API.get(id=api_id)
        except peewee.DoesNotExist:
            self.logger.error('Chat unregistered')
            response_text = 'Configure me first'
        except BarreneroRequestException as e:
            self.logger.exception(e.message)
            response_text = e.message
        else:
            try:
                data = Barrenero.ether(api.url, api.token)

                response_text = f'*Ether miner*\n' \
                                f' - Status: {data["active"]}\n\n' \
                                f'*Hashrate*\n' \
                                + '\n'.join([f' - Graphic card #{h["graphic_card"]}: `{h["hashrate"]:.2f} MH/s`'
                                             for h in data['hashrate']])
            except BarreneroRequestException as e:
                self.logger.error(e.message)
                response_text = f'*API {api.name} - Ether miner*\n{e.message}'
            except (KeyError, TypeError):
                response_text = f'*API {api.name} - Ether miner*\nCannot retrieve Ether miner status'
                self.logger.error('Barrenero API wrong response for Ether miner status: %s', str(data))

        bot.edit_message_text(text=response_text, parse_mode=ParseMode.MARKDOWN, chat_id=chat_id,
                              message_id=query.message.message_id)

    def ether_job_status(self, bot, job):
        """
        Check miner status
        """
        # Create new state machines
        new_machines = {a: StatusStateMachine('Ether', a.name)
                        for a in API.select().where(API.superuser == True).join(Chat)
                        if a not in self.ether_status_machine}
        self.ether_status_machine.update(new_machines)

        for api, status in self.ether_status_machine.items():
            try:
                data = Barrenero.ether(api.url, api.token)

                if data['active']:
                    status.start(bot=bot, chat=api.chat.id)
                else:
                    status.stop(bot=bot, chat=api.chat.id)
            except BarreneroRequestException:
                if status.is_active:
                    bot.send_message(api.chat.id, f'Cannot access `{api.name}`', parse_mode=ParseMode.MARKDOWN)
                    status.stop(bot=bot, chat=api.chat.id)

    def add_ether_command(self):
        self.dispatcher.add_handler(CommandHandler('ether', self.ether))
        self.dispatcher.add_handler(CallbackQueryHandler(self.ether_restart, pass_groups=True,
                                                         pattern=r'\[ether_restart\]\[(\d+)\]'))
        self.dispatcher.add_handler(CallbackQueryHandler(self.ether_status, pass_groups=True,
                                                         pattern=r'\[ether_status\]\[(\d+)\]'))
        self.dispatcher.add_handler(CallbackQueryHandler(self.ether_miner_choice, pass_groups=True,
                                                         pattern=r'\[ether_(restart|status)\]$'))
        self.dispatcher.add_handler(CallbackQueryHandler(self.ether_nanopool, pattern=r'\[ether_nanopool\]'))

    def add_ether_jobs(self):
        self.updater.job_queue.run_repeating(self.ether_job_status, 60.0)
