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
        else:
            response_text = ''
            for api in chat.apis:
                try:
                    status = Barrenero.miner(api.url, api.token)
                except BarreneroRequestException as e:
                    self.logger.exception(e.message)
                    response_text += f'*API {api.name}*\n{e.message}\n\n'
                else:
                    response_text += f'*API {api.name} - Services*\n'
                    response_text += '\n'.join([f' - {service["name"]}: `{service["status"]}`'
                                                for service in status['services']])

                    for graphic in status['graphics']:
                        response_text += f'\n\n*API {api.name} - Graphic card #{graphic["id"]}*\n'
                        response_text += f' - Power: `{graphic["power"]} W`\n'
                        response_text += f' - Fan speed: `{graphic["fan"]} %`\n'
                        response_text += f' - GPU: `{graphic["gpu_usage"]} %` - `{graphic["gpu_clock"]} Mhz`\n'
                        response_text += f' - MEM: `{graphic["mem_usage"]} %` - `{graphic["mem_clock"]} Mhz`\n\n'
        finally:
            bot.send_message(text=response_text, parse_mode=ParseMode.MARKDOWN, chat_id=chat_id)

    def add_miner_command(self):
        self.dispatcher.add_handler(CommandHandler('miner', self.miner))
