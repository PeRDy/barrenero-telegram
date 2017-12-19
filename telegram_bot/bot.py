import logging
from configparser import ConfigParser
from enum import Enum, IntEnum

import peewee
import requests
from telegram import ParseMode, ReplyKeyboardMarkup
from telegram.ext import CommandHandler, ConversationHandler, Filters, MessageHandler, Updater
from telegram.ext.regexhandler import RegexHandler

from telegram_bot.ether import EtherMixin
from telegram_bot.miner import MinerMixin
from telegram_bot.persistence import Chat, initialize_db, API
from telegram_bot.storj import StorjMixin
from telegram_bot.wallet import WalletMixin


class StartState(IntEnum):
    CHOICE_ROOT = 1
    CHOICE_ADD_API = 2
    CHOICE_URL = 3
    CHOICE_USERNAME = 4
    CHOICE_PASSWORD = 5
    CHOICE_WALLET = 6
    CHOICE_SUPERUSER = 7
    CHOICE_REMOVE_API = 8


class StartOptions(Enum):
    ADD_API = 'Add API'
    REMOVE_API = 'Remove API'
    CURRENT_CONFIG = 'Show current config'
    URL = 'URL'
    USERNAME = 'Username'
    PASSWORD = 'Password'
    WALLET = 'Wallet'
    SUPERUSER = 'Superuser'
    CURRENT_CHANGES = 'Show current changes'
    DONE = 'Done!'
    FINISH = 'Finish'


class TelegramBot(MinerMixin, EtherMixin, StorjMixin, WalletMixin):
    HELP_TEXT = """I can show you Barrenero's current status, as well as some information of different services related.

Lets start setting up some parameters with /start

*Barrenero*
/miner - Barrenero's current status.

*Services*
/ether - Ether Miner info.
/storj - Storj Miner info.
/wallet - Ethereum Wallet balance.

Help us donating to support this project:
 - Ether: `0x566d41b925ed1d9f643748d652f4e66593cba9c9`
 - Bitcoin: `1Jtj2m65DN2UsUzxXhr355x38T6pPGhqiA`
 - PayPal: `barrenerobot@gmail.com`
"""

    def __init__(self, config='setup.cfg'):
        # Read bot config from file
        config_from_file = ConfigParser()
        config_from_file.read(config)
        self._telegram_token = config_from_file.get('telegram', 'token', fallback=None)
        self._max_idle = config_from_file.getint('telegram', 'max_idle', fallback=None)

        # Initialize DB
        initialize_db()

        # Store for chat based config, loaded from database
        self.tmp_config = {}  # Config dict for keeping temporal data before registering in API

        self.logger = logging.getLogger('telegram')

        self.updater = Updater(token=self._telegram_token)
        self.dispatcher = self.updater.dispatcher

    def help(self, bot, update):
        """
        Shows help message.
        """
        chat_id = update.message.chat_id
        bot.send_message(chat_id, self.HELP_TEXT, parse_mode=ParseMode.MARKDOWN)

        return StartState.CHOICE_ROOT

    def start(self, bot, update):
        """
        Start bot configuration.
        """
        keyboard = ((StartOptions.ADD_API.value,),
                    (StartOptions.REMOVE_API.value,),
                    (StartOptions.CURRENT_CONFIG.value, StartOptions.FINISH.value,))
        markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)

        update.message.reply_text('Select an option.', reply_markup=markup)

        return StartState.CHOICE_ROOT

    def choice_add_api(self, bot, update):
        """
        Asks for a new Barrenero API config.
        """
        keyboard = (
            (StartOptions.URL.value, StartOptions.USERNAME.value, StartOptions.PASSWORD.value),
            (StartOptions.WALLET.value, StartOptions.SUPERUSER.value),
            (StartOptions.CURRENT_CHANGES.value, StartOptions.DONE.value)
        )
        markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)

        update.message.reply_text("We need to specify some parameters to add a new Barrenero API.\n"
                                  'Select an option.', reply_markup=markup)

        return StartState.CHOICE_ADD_API

    def choice_url(self, bot, update):
        """
        Asks for Barrenero API url.
        """
        update.message.reply_text('Introduce the *url* from Barrenero API', parse_mode=ParseMode.MARKDOWN)

        return StartState.CHOICE_URL

    def choice_username(self, bot, update):
        """
        Asks for username.
        """
        update.message.reply_text('What should be your *username*?', parse_mode=ParseMode.MARKDOWN)

        return StartState.CHOICE_USERNAME

    def choice_password(self, bot, update):
        """
        Asks for password.
        """
        update.message.reply_text('Introduce the *password* that you will use to login in Barrenero API',
                                  parse_mode=ParseMode.MARKDOWN)

        return StartState.CHOICE_PASSWORD

    def choice_wallet(self, bot, update):
        """
        Asks for nanopool token.
        """
        update.message.reply_text('What is your *Wallet* account? It must begin with `0x`.',
                                  parse_mode=ParseMode.MARKDOWN)

        return StartState.CHOICE_WALLET

    def choice_superuser(self, bot, update):
        """
        Asks for etherscan token.
        """
        update.message.reply_text('Introduce API *superuser password*.', parse_mode=ParseMode.MARKDOWN)

        return StartState.CHOICE_SUPERUSER

    def choice_current_changes(self, bot, update):
        """
        Shows current config.
        """
        chat_id = update.message.chat_id
        tmp_config = self.tmp_config.get(chat_id, {})

        response_text = f'*New Configuration*\n' \
                        f' - API: `{tmp_config.get("url", "Not configured")}`\n' \
                        f' - Username: `{tmp_config.get("username", "Not configured")}`\n' \
                        f' - Password: `{tmp_config.get("password", "Not configured")}`\n' \
                        f' - Wallet: `{tmp_config.get("wallet", "Not configured")}`\n' \
                        f' - Superuser password: `{tmp_config.get("api_password", "Not configured")}`'

        update.message.reply_text(response_text, parse_mode=ParseMode.MARKDOWN)

        return StartState.CHOICE_ADD_API

    def config_url(self, bot, update):
        text = update.message.text
        chat_id = update.message.chat_id

        if chat_id not in self.tmp_config:
            self.tmp_config[chat_id] = {}

        if text[-1] == '/':
            text = text[:-1]

        self.tmp_config[chat_id]['url'] = text

        update.message.reply_text('Keep Barrenero API *url*', parse_mode=ParseMode.MARKDOWN)

        return StartState.CHOICE_ADD_API

    def config_username(self, bot, update):
        text = update.message.text
        chat_id = update.message.chat_id

        if chat_id not in self.tmp_config:
            self.tmp_config[chat_id] = {}

        self.tmp_config[chat_id]['username'] = text

        update.message.reply_text('Keep *username* for registering in API', parse_mode=ParseMode.MARKDOWN)

        return StartState.CHOICE_ADD_API

    def config_password(self, bot, update):
        text = update.message.text
        chat_id = update.message.chat_id

        if chat_id not in self.tmp_config:
            self.tmp_config[chat_id] = {}

        self.tmp_config[chat_id]['password'] = text

        update.message.reply_text('Keep *password* for registering in API', parse_mode=ParseMode.MARKDOWN)

        return StartState.CHOICE_ADD_API

    def config_wallet(self, bot, update):
        """
        Sets wallet configuration for this chat.
        """
        text = update.message.text
        chat_id = update.message.chat_id

        try:
            assert text.startswith('0x')
            assert len(text) == 42
            assert int(text, 16)

            if chat_id not in self.tmp_config:
                self.tmp_config[chat_id] = {}

            self.tmp_config[chat_id]['wallet'] = text

            response_text = 'Your *Wallet* address has been configured properly.'
        except AssertionError:
            response_text = f'Wallet address `{text}` is wrong.\n' \
                            f'It must begin with `0x` and have an exact length of 40 chars.'

        update.message.reply_text(response_text, parse_mode=ParseMode.MARKDOWN)

        return StartState.CHOICE_ADD_API

    def config_superuser(self, bot, update):
        text = update.message.text
        chat_id = update.message.chat_id

        if chat_id not in self.tmp_config:
            self.tmp_config[chat_id] = {}

        self.tmp_config[chat_id]['api_password'] = text

        update.message.reply_text('Keep *superuser password* for registering in API', parse_mode=ParseMode.MARKDOWN)

        return StartState.CHOICE_ADD_API

    def _get_token_or_register(self, chat_id):
        api_url = self.tmp_config[chat_id]['url']
        username = self.tmp_config[chat_id]['username'],
        password = self.tmp_config[chat_id]['password'],
        account = self.tmp_config[chat_id].get('wallet'),
        api_password = self.tmp_config[chat_id].get('api_password'),

        try:
            # Try to register user
            url = f'{api_url}/api/v1/auth/register/'
            data = {'username': username, 'password': password, 'account': account, 'api_password': api_password}
            response_register = requests.post(url=url, data=data)

            # If user is registered, try to get token using username and password
            if response_register.status_code == 409:
                url = f'{api_url}/api/v1/auth/user/'
                data = {'username': username, 'password': password}

                response_user = requests.post(url=url, data=data)
                response_user.raise_for_status()
                payload = response_user.json()
            else:
                response_register.raise_for_status()
                payload = response_register.json()
        except requests.HTTPError:
            self.logger.exception('Cannot retrieve Barrenero API token')
            raise
        else:
            config = {
                'url': api_url,
                'token': payload['token'],
                'superuser': payload['is_api_superuser'],
            }

        return config

    def add_api(self, bot, update):
        """
        Adds configured api.
        """
        chat_id = update.message.chat_id

        try:
            chat, _ = Chat.get_or_create(id=chat_id, defaults={'last_transaction': None})

            config = self._get_token_or_register(chat_id)

            API.create(url=config['url'], token=config['token'], superuser=config['superuser'], chat=chat)
        except:
            self.logger.exception('Cannot register Barrenero API')
        else:
            update.message.reply_text('Api stored successfully')

        return self.start(bot, update)

    def choice_remove_api(self, bot, update):
        """
        Asks for removing a Barrenero API already configured.
        """
        chat_id = update.message.chat_id
        try:
            chat = Chat.get(id=chat_id)
        except peewee.DoesNotExist:
            update.message.reply_text('There is not a Barrenero API configured yet')

            result = self.start(bot, update)
        else:
            buttons = [str(i.id) for i in chat.apis]
            keyboard = [buttons[i:i + 4] for i in range(0, len(buttons), 4)] if len(buttons) >= 4 else [buttons]
            keyboard.append([StartOptions.DONE.value])
            markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)

            response_text = f'*APIs configured*\n' + '\n'.join([f'*{a.id}*: `{a.url}`' for a in chat.apis])

            update.message.reply_text(response_text, parse_mode=ParseMode.MARKDOWN, reply_markup=markup)

            result = StartState.CHOICE_REMOVE_API

        return result

    def remove_api(self, bot, update):
        text = update.message.text
        chat_id = update.message.chat_id

        try:
            chat = Chat.get(id=chat_id)
            API.get(id=text, chat=chat).delete_instance()
        except:
            self.logger.exception('Cannot remove Barrenero API')
            update.message.reply_text('Cannot remove Barrenero API')

        return StartState.CHOICE_REMOVE_API

    def choice_current_config(self, bot, update):
        """
        Shows current config.
        """
        chat_id = update.message.chat_id

        try:
            chat = Chat.get(id=chat_id)
        except peewee.DoesNotExist:
            response_text = 'No configuration found'
        else:
            response_text = f'*Current config*\n' \
                            f' - Last Transaction: `{chat.last_transaction}`\n\n'

            for i, api in enumerate(chat.apis, 1):
                response_text += f'*API #{i}*\n' \
                                 f' - URL: `{api.url}`\n' \
                                 f' - Token: `{api.token}`\n' \
                                 f' - Superuser: `{"Yes" if api.superuser else "No"}`\n\n'

        update.message.reply_text(response_text, parse_mode=ParseMode.MARKDOWN)

        return StartState.CHOICE_ROOT

    def config_done(self, bot, update):
        """
        Finishes configuration process.
        """
        update.message.reply_text("Configuration completed!")

        return ConversationHandler.END

    def error(self, bot, update, error):
        """
        Error handler.
        """
        self.logger.error('Update "%s" caused error "%s"', update, error)

    def run(self):
        """
        Setup the bot
        """
        # Help command
        self.dispatcher.add_handler(CommandHandler('help', self.help))

        # Start command
        self.dispatcher.add_handler(ConversationHandler(
            entry_points=[CommandHandler('start', self.start)],
            states={
                StartState.CHOICE_ROOT: [
                    RegexHandler(f'^{StartOptions.ADD_API.value}$', self.choice_add_api),
                    RegexHandler(f'^{StartOptions.REMOVE_API.value}$', self.choice_remove_api),
                    RegexHandler(f'^{StartOptions.CURRENT_CONFIG.value}$', self.choice_current_config),
                ],
                StartState.CHOICE_ADD_API: [
                    RegexHandler(f'^{StartOptions.URL.value}$', self.choice_url),
                    RegexHandler(f'^{StartOptions.USERNAME.value}$', self.choice_username),
                    RegexHandler(f'^{StartOptions.PASSWORD.value}$', self.choice_password),
                    RegexHandler(f'^{StartOptions.WALLET.value}$', self.choice_wallet),
                    RegexHandler(f'^{StartOptions.SUPERUSER.value}$', self.choice_superuser),
                    RegexHandler(f'^{StartOptions.CURRENT_CONFIG.value}$', self.choice_current_changes),
                    RegexHandler(f'^{StartOptions.DONE.value}$', self.add_api),
                ],
                StartState.CHOICE_REMOVE_API: [
                    RegexHandler(f'^{StartOptions.DONE.value}$', self.start),
                    MessageHandler(Filters.text, self.remove_api),
                ],
                StartState.CHOICE_URL: [
                    MessageHandler(Filters.text, self.config_url)
                ],
                StartState.CHOICE_USERNAME: [
                    MessageHandler(Filters.text, self.config_username)
                ],
                StartState.CHOICE_PASSWORD: [
                    MessageHandler(Filters.text, self.config_password)
                ],
                StartState.CHOICE_WALLET: [
                    MessageHandler(Filters.text, self.config_wallet)
                ],
                StartState.CHOICE_SUPERUSER: [
                    MessageHandler(Filters.text, self.config_superuser)
                ]
            },
            fallbacks=[RegexHandler(f'^{StartOptions.FINISH.value}$', self.config_done)]
        ))

        # Miner command
        # self.add_miner_command()

        # Ether command
        # self.add_ether_command()
        # self.add_ether_jobs()

        # Storj command
        # self.add_storj_command()
        # self.add_storj_jobs()

        # Wallet command
        # self.add_wallet_command()
        # self.add_wallet_jobs()

        # Error handler
        self.dispatcher.add_error_handler(self.error)

        try:
            self.updater.start_polling()

            self.updater.idle()
        except:
            self.updater.stop()
