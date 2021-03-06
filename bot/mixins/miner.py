import peewee
from telegram import ChatAction, InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.ext import CallbackQueryHandler, CommandHandler

from bot.api import Barrenero
from bot.exceptions import BarreneroRequestException
from bot.models import API, Chat


class MinerMixin:
    def miner(self, bot, update):
        """
        Asks for a miner.
        """
        chat_id = update.message.chat.id
        bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
        try:
            chat = Chat.get(id=chat_id)

            buttons = [InlineKeyboardButton(api.name, callback_data=f'[miner_status][{api.id}]')
                       for api in chat.apis if api.superuser]
            keyboard = [buttons[i:max(len(buttons), i + 4)] for i in range(0, len(buttons), 4)]
            reply_markup = InlineKeyboardMarkup(keyboard)
        except peewee.DoesNotExist:
            self.logger.error('Chat unregistered')
            response_text = 'Configure me first'
            bot.send_message(chat_id, response_text)
        else:
            if reply_markup:
                bot.send_message(text='Select miner:', reply_markup=reply_markup, chat_id=chat_id)
            else:
                bot.send_message(text='No options available', chat_id=chat_id)

    def miner_status(self, bot, update, groups):
        """
        Query Miner status and return it properly formatted.
        """
        query = update.callback_query
        api_id = groups[0]
        chat_id = query.message.chat_id

        bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)

        try:
            api = API.get(id=api_id)

            data = Barrenero.miner(api.url, api.token)

            response_text = f'*API {api.name}*\n'
            response_text += '*Services*\n'
            response_text += '\n'.join([f' - {service["name"]}: `{service["status"]}`'
                                        for service in data['services']])

            for graphic in data['graphics']:
                response_text += f'\n\n*Graphic card #{graphic["id"]}*\n'
                response_text += f' - Power: `{graphic["power"]} W`\n'
                response_text += f' - Fan speed: `{graphic["fan"]} %`\n'
                response_text += f' - GPU: `{graphic["gpu_usage"]} %` - `{graphic["gpu_clock"]} Mhz`\n'
                response_text += f' - MEM: `{graphic["mem_usage"]} %` - `{graphic["mem_clock"]} Mhz`'
        except peewee.DoesNotExist:
            self.logger.error('Chat unregistered')
            response_text = 'Configure me first'
        except BarreneroRequestException as e:
            self.logger.exception(e.message)
            response_text = f'*API {api.name} - Ether miner*\n{e.message}'
        except:
            response_text = f'*API {api.name} - Ether miner*\nCannot retrieve Ether miner status'
            self.logger.exception('Barrenero API wrong response for Ether miner status: %s', str(data))

        bot.edit_message_text(text=response_text, parse_mode=ParseMode.MARKDOWN, chat_id=chat_id,
                              message_id=query.message.message_id)

    def add_miner_command(self):
        self.updater.dispatcher.add_handler(CommandHandler('miner', self.miner))
        self.updater.dispatcher.add_handler(CallbackQueryHandler(self.miner_status, pass_groups=True,
                                                                 pattern=r'\[miner_status\]\[(\d+)\]'))
