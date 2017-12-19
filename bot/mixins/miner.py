import peewee
import requests
from telegram import ChatAction, ParseMode
from telegram.ext import CommandHandler

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
            status = self._status(chat)
        except peewee.DoesNotExist:
            self.logger.error('Chat unregistered')
            response_text = 'Configure me first'
        else:
            response_text = '*Services*\n'
            response_text += '\n'.join([f' - {service["name"]}: `{service["status"]}`'
                                        for service in status['services']])

            for graphic_card in status['graphics']:
                response_text += f'\n\n*Graphic card #{graphic_card["id"]}*\n'
                response_text += f' - Power: `{graphic_card["power"]} W`\n'
                response_text += f' - Fan speed: `{graphic_card["fan"]} %`\n'
                response_text += f' - GPU: `{graphic_card["gpu_usage"]} %` - `{graphic_card["gpu_clock"]} Mhz`\n'
                response_text += f' - MEM: `{graphic_card["mem_usage"]} %` - `{graphic_card["mem_clock"]} Mhz`'
        finally:
            bot.send_message(text=response_text, parse_mode=ParseMode.MARKDOWN, chat_id=chat_id)

    def add_miner_command(self):
        self.dispatcher.add_handler(CommandHandler('miner', self.miner))

    def _status(self, chat: 'Chat'):
        url = f'{self._api}/api/v1/status'
        headers = {'Authorization': f'Token {chat.token}'}
        try:
            response = requests.get(url=url, headers=headers)
            response.raise_for_status()
            status = response.json()
        except requests.HTTPError:
            self.logger.exception('Cannot retrieve Barrenero status')
            status = None

        return status
