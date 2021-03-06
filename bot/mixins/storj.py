import threading

import peewee
from telegram import ChatAction, InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.ext import CallbackQueryHandler, CommandHandler

from bot.api import Barrenero
from bot.exceptions import BarreneroRequestException
from bot.models import API, Chat
from bot.state_machine import StatusStateMachine

status_machines = {}
lock = threading.RLock()


class StorjMixin:
    def storj(self, bot, update):
        """
        Call for Storj miner status and restarting service.
        """
        chat_id = update.message.chat.id
        bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)

        keyboard = [
            [
                InlineKeyboardButton("Status", callback_data='[storj_status]'),
            ],
            [
                InlineKeyboardButton("Restart", callback_data='[storj_restart]'),
            ],
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        bot.send_message(chat_id, 'Select an option:', reply_markup=reply_markup)

    def storj_miner_choice(self, bot, update, groups):
        """
        Select a miner to do following action.
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
            buttons = [InlineKeyboardButton(api.name, callback_data=f'[storj_{action}][{api.id}]')
                       for api in chat.apis if api.superuser]
            keyboard = [buttons[i:max(len(buttons), i + 4)] for i in range(0, len(buttons), 4)]
            reply_markup = InlineKeyboardMarkup(keyboard)
        else:
            reply_markup = None

        if reply_markup:
            bot.edit_message_text(text='Select miner to restart:', reply_markup=reply_markup, chat_id=chat_id,
                                  message_id=query.message.message_id)
        else:
            bot.edit_message_text(text='No options available', chat_id=chat_id, message_id=query.message.message_id)

    def storj_restart(self, bot, update, groups):
        """
        Restart storj service.
        """
        query = update.callback_query
        api_id = groups[0]
        chat_id = query.message.chat_id

        bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)

        try:
            api = API.get(id=api_id)

            Barrenero.restart(api.url, api.token, 'Storj')

            response_text = f'*API {api.name}*\n' \
                            f'Restarting Storj.'
        except peewee.DoesNotExist:
            self.logger.error('Chat unregistered')
            response_text = 'Configure me first'
        except BarreneroRequestException as e:
            self.logger.exception(e.message)
            response_text = e.message
        except:
            self.logger.exception('Cannot restart API %s Storj miner', api.name)
            response_text = f'*API {api.name} - Storj miner*\nCannot restart miner'

        bot.edit_message_text(text=response_text, parse_mode=ParseMode.MARKDOWN, chat_id=chat_id,
                              message_id=query.message.message_id)

    def storj_status(self, bot, update, groups):
        """
        Check Storj miner status.
        """
        query = update.callback_query
        api_id = groups[0]
        chat_id = query.message.chat_id

        bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)

        try:
            api = API.get(id=api_id)
            data = Barrenero.storj(api.url, api.token)

            nodes_status = []
            for node in data:
                shared = node['shared'] if node['shared'] is not None else 'Unknown'
                shared_percent = f'{node["shared_percent"]}%' if node['shared_percent'] is not None else 'Unknown'
                data_received = node['data_received'] if node['data_received'] is not None else 'Unknown'
                delta = f'{node["delta"]:d} ms' if node['delta'] is not None else 'Unknown'
                response_time = f'{node["response_time"]:.2f} ms' if node['response_time'] is not None else 'Unknown'
                reputation = f'{node["reputation"]:d}/5000' if node['reputation'] is not None else 'Unknown'
                version = node["version"] if node['version'] is not None else 'Unknown'
                nodes_status.append(
                    f'*Storj node #{node["id"]}*\n'
                    f' - Status: `{node["status"]}`\n'
                    f' - Uptime: `{node["uptime"]} ({node["restarts"]} restarts)`\n'
                    f' - Shared: `{shared} ({shared_percent})`\n'
                    f' - Data received: `{data_received}`\n'
                    f' - Peers/Allocs: `{node["peers"]:d}` / `{node["allocs"]:d}`\n'
                    f' - Delta: `{delta}`\n'
                    f' - Path: `{node["config_path"]}`\n'
                    f' - Response Time: `{response_time}`\n'
                    f' - Reputation: `{reputation}`\n'
                    f' - Version: `{version}`')
            response_text = f'*API {api.name}*\n' + '\n\n'.join(nodes_status)
        except peewee.DoesNotExist:
            self.logger.error('Chat unregistered')
            response_text = 'Configure me first'
        except BarreneroRequestException as e:
            self.logger.exception(e.message)
            response_text = f'*API {api}*\nCannot retrieve Storj miner status'
        except:
            self.logger.exception('Error retrieving storj status')
            response_text = 'Cannot retrieve storj status'

        bot.edit_message_text(text=response_text, parse_mode=ParseMode.MARKDOWN, chat_id=chat_id,
                              message_id=query.message.message_id)

    def storj_job_status(self, bot, job):
        """
        Check miner status
        """
        self.logger.debug('Job: Check Storj status')

        # Create new state machines
        global status_machines

        with lock:
            new_machines = {a: StatusStateMachine('Storj', a.name)
                            for a in API.select().where(API.superuser == True).join(Chat)
                            if a not in status_machines}
            status_machines.update(new_machines)

            self.logger.debug('Storj Status Machines: %s', str(status_machines))

            for api, status in status_machines.items():
                try:
                    data = Barrenero.storj(api.url, api.token)

                    node_status = {d['status'] for d in data}
                    if node_status == {'running'}:
                        status.start(bot=bot, chat=api.chat.id)
                    else:
                        status.stop(bot=bot, chat=api.chat.id)
                except BarreneroRequestException:
                    if status.is_active:
                        bot.send_message(api.chat.id, f'Cannot access `{api.name}`', parse_mode=ParseMode.MARKDOWN)
                        status.stop(bot=bot, chat=api.chat.id)

    def add_storj_command(self):
        self.updater.dispatcher.add_handler(CommandHandler('storj', self.storj))
        self.updater.dispatcher.add_handler(CallbackQueryHandler(self.storj_restart, pass_groups=True,
                                                                 pattern=r'\[storj_restart\]\[(\d+)\]'))
        self.updater.dispatcher.add_handler(CallbackQueryHandler(self.storj_status, pass_groups=True,
                                                                 pattern=r'\[storj_status\]\[(\d+)\]'))
        self.updater.dispatcher.add_handler(CallbackQueryHandler(self.storj_miner_choice, pass_groups=True,
                                                                 pattern=r'\[storj_(status|restart)\]$'))

    def add_storj_jobs(self):
        self.updater.job_queue.run_repeating(self.storj_job_status, interval=300.0)
