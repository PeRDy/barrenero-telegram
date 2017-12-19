import peewee
import requests
from telegram import ChatAction, ParseMode
from telegram.ext import CommandHandler

from bot.api import Barrenero
from bot.exceptions import BarreneroRequestException
from bot.models import Chat


class MinerMixin:
    def miner(self, bot, update):
        """
        Query Miner status and return it properly formatted.
        """
        chat_id = update.message.chat_id

        bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)

        try:
            chat = Chat.get(id=chat_id)
        except peewee.DoesNotExist:
            self.logger.error('Chat unregistered')
            response_text = 'Configure me first'
        except BarreneroRequestException as e:
            self.logger.exception(e.message)
            response_text = e.message
        else:
            all_messages = []
            for api in chat.apis:
                try:
                    status = Barrenero.miner(api.url, api.token)
                except BarreneroRequestException as e:
                    self.logger.exception(e.message)
                    status_message = f'*API {api.name}*\n{e.message}'
                else:
                    status_message = f'*API {api.name} - Services*\n'
                    status_message += '\n'.join([f' - {service["name"]}: `{service["status"]}`'
                                                for service in status['services']])

                    for graphic in status['graphics']:
                        status_message += f'\n\n*API {api.name} - Graphic card #{graphic["id"]}*\n'
                        status_message += f' - Power: `{graphic["power"]} W`\n'
                        status_message += f' - Fan speed: `{graphic["fan"]} %`\n'
                        status_message += f' - GPU: `{graphic["gpu_usage"]} %` - `{graphic["gpu_clock"]} Mhz`\n'
                        status_message += f' - MEM: `{graphic["mem_usage"]} %` - `{graphic["mem_clock"]} Mhz`'
                all_messages.append(status_message)
            response_text = '\n\n'.join(all_messages)

        bot.send_message(text=response_text, parse_mode=ParseMode.MARKDOWN, chat_id=chat_id)

    def add_miner_command(self):
        self.dispatcher.add_handler(CommandHandler('miner', self.miner))
