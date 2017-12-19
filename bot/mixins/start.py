from enum import Enum, IntEnum

import peewee
from telegram import ParseMode, ReplyKeyboardMarkup
from telegram.ext import CommandHandler, ConversationHandler, Filters, MessageHandler
from telegram.ext.regexhandler import RegexHandler

from bot.api import Barrenero
from bot.models import API, Chat


class StartState(IntEnum):
    CHOICE_ROOT = 1
    CHOICE_ADD_API = 2
    CHOICE_URL = 3
    CHOICE_NAME = 4
    CHOICE_USERNAME = 5
    CHOICE_PASSWORD = 6
    CHOICE_WALLET = 7
    CHOICE_SUPERUSER = 8
    CHOICE_REMOVE_API = 9


class StartOptions(Enum):
    ADD_API = 'Add API'
    REMOVE_API = 'Remove API'
    CURRENT_CONFIG = 'Show current config'
    URL = 'API URL'
    NAME = 'API Name'
    USERNAME = 'Username'
    PASSWORD = 'Password'
    WALLET = 'Wallet'
    SUPERUSER = 'Superuser'
    CURRENT_CHANGES = 'Show current changes'
    DONE = 'Done!'
    FINISH = 'Finish'


class StartMixin:
    def __init__(self):
        # Config dict for keeping temporal data before registering in API
        self.tmp_config = {}

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

    def _add_api_choice(self, bot, update):
        """
        Asks for a new Barrenero API config.
        """
        keyboard = (
            (StartOptions.URL.value, StartOptions.NAME.value),
            (StartOptions.USERNAME.value, StartOptions.PASSWORD.value),
            (StartOptions.WALLET.value, StartOptions.SUPERUSER.value),
            (StartOptions.CURRENT_CHANGES.value, StartOptions.DONE.value)
        )
        markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)

        update.message.reply_text("We need to specify some parameters to add a new Barrenero API.\n"
                                  'Select an option.', reply_markup=markup)

        return StartState.CHOICE_ADD_API

    def _add_api_choice_url(self, bot, update):
        """
        Asks for Barrenero API url.
        """
        update.message.reply_text('Introduce the *url* from Barrenero API', parse_mode=ParseMode.MARKDOWN)

        return StartState.CHOICE_URL

    def _add_api_choice_name(self, bot, update):
        """
        Asks for Barrenero API name.
        """
        update.message.reply_text('Introduce the *name* for Barrenero API', parse_mode=ParseMode.MARKDOWN)

        return StartState.CHOICE_NAME

    def _add_api_choice_username(self, bot, update):
        """
        Asks for username.
        """
        update.message.reply_text('What should be your *username*?', parse_mode=ParseMode.MARKDOWN)

        return StartState.CHOICE_USERNAME

    def _add_api_choice_password(self, bot, update):
        """
        Asks for password.
        """
        update.message.reply_text('Introduce the *password* that you will use to login in Barrenero API',
                                  parse_mode=ParseMode.MARKDOWN)

        return StartState.CHOICE_PASSWORD

    def _add_api_choice_wallet(self, bot, update):
        """
        Asks for nanopool token.
        """
        update.message.reply_text('What is your *Wallet* account? It must begin with `0x`.',
                                  parse_mode=ParseMode.MARKDOWN)

        return StartState.CHOICE_WALLET

    def _add_api_choice_superuser(self, bot, update):
        """
        Asks for etherscan token.
        """
        update.message.reply_text('Introduce API *superuser password*.', parse_mode=ParseMode.MARKDOWN)

        return StartState.CHOICE_SUPERUSER

    def _add_api_choice_current_changes(self, bot, update):
        """
        Shows current config.
        """
        chat_id = update.message.chat_id
        tmp_config = self.tmp_config.get(chat_id, {})

        response_text = f'*New Configuration*\n' \
                        f' - URL: `{tmp_config.get("url", "Not configured")}`\n' \
                        f' - Name: `{tmp_config.get("name", "Not configured")}`\n' \
                        f' - Username: `{tmp_config.get("username", "Not configured")}`\n' \
                        f' - Password: `{tmp_config.get("password", "Not configured")}`\n' \
                        f' - Wallet: `{tmp_config.get("wallet", "Not configured")}`\n' \
                        f' - Superuser password: `{tmp_config.get("api_password", "Not configured")}`'

        update.message.reply_text(response_text, parse_mode=ParseMode.MARKDOWN)

        return StartState.CHOICE_ADD_API

    def _add_api_config_url(self, bot, update):
        text = update.message.text
        chat_id = update.message.chat_id

        if chat_id not in self.tmp_config:
            self.tmp_config[chat_id] = {}

        if text[-1] == '/':
            text = text[:-1]

        self.tmp_config[chat_id]['url'] = text

        update.message.reply_text('Keep Barrenero API *url*', parse_mode=ParseMode.MARKDOWN)

        return StartState.CHOICE_ADD_API

    def _add_api_config_name(self, bot, update):
        text = update.message.text
        chat_id = update.message.chat_id

        if chat_id not in self.tmp_config:
            self.tmp_config[chat_id] = {}

        self.tmp_config[chat_id]['name'] = text

        update.message.reply_text('Keep Barrenero API *name*', parse_mode=ParseMode.MARKDOWN)

        return StartState.CHOICE_ADD_API

    def _add_api_config_username(self, bot, update):
        text = update.message.text
        chat_id = update.message.chat_id

        if chat_id not in self.tmp_config:
            self.tmp_config[chat_id] = {}

        self.tmp_config[chat_id]['username'] = text

        update.message.reply_text('Keep *username* for registering in API', parse_mode=ParseMode.MARKDOWN)

        return StartState.CHOICE_ADD_API

    def _add_api_config_password(self, bot, update):
        text = update.message.text
        chat_id = update.message.chat_id

        if chat_id not in self.tmp_config:
            self.tmp_config[chat_id] = {}

        self.tmp_config[chat_id]['password'] = text

        update.message.reply_text('Keep *password* for registering in API', parse_mode=ParseMode.MARKDOWN)

        return StartState.CHOICE_ADD_API

    def _add_api_config_wallet(self, bot, update):
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

    def _add_api_config_superuser(self, bot, update):
        text = update.message.text
        chat_id = update.message.chat_id

        if chat_id not in self.tmp_config:
            self.tmp_config[chat_id] = {}

        self.tmp_config[chat_id]['api_password'] = text

        update.message.reply_text('Keep *superuser password* for registering in API', parse_mode=ParseMode.MARKDOWN)

        return StartState.CHOICE_ADD_API

    def _add_api_config_done(self, bot, update):
        """
        Adds configured api.
        """
        chat_id = update.message.chat_id

        try:
            chat, _ = Chat.get_or_create(id=chat_id, defaults={'last_transaction': None})

            config = Barrenero.get_token_or_register(
                url=self.tmp_config[chat_id]['url'],
                username=self.tmp_config[chat_id]['username'],
                password=self.tmp_config[chat_id]['password'],
                account=self.tmp_config[chat_id]['wallet'],
                api_password=self.tmp_config[chat_id]['api_password'],
            )

            API.create(
                name=self.tmp_config[chat_id]['name'],
                url=self.tmp_config[chat_id]['url'],
                token=config['token'],
                superuser=config['superuser'],
                chat=chat
            )
        except:
            self.logger.exception('Cannot register Barrenero API')
        else:
            update.message.reply_text('Api stored successfully')

        return self.start(bot, update)

    def _remove_api_choice(self, bot, update):
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
            keyboard = [buttons[i:min(len(buttons), i + 4)] for i in range(0, len(buttons), 4)]
            keyboard.append([StartOptions.DONE.value])
            markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)

            response_text = f'*APIs configured*\n' + '\n'.join([f'*{a.id}*: `{a.url}`' for a in chat.apis])

            update.message.reply_text(response_text, parse_mode=ParseMode.MARKDOWN, reply_markup=markup)

            result = StartState.CHOICE_REMOVE_API

        return result

    def _remove_api_config(self, bot, update):
        text = update.message.text
        chat_id = update.message.chat_id

        try:
            chat = Chat.get(id=chat_id)
            api = API.get(id=text, chat=chat)
            name = api.name
            api.delete_instance()
            update.message.reply_text(f'Barrenero API `{name}` removed successfully')
        except:
            self.logger.exception('Cannot remove Barrenero API')
            update.message.reply_text('Cannot remove Barrenero API')

        return StartState.CHOICE_REMOVE_API

    def _current_config_choice(self, bot, update):
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
                                 f' - Name: `{api.name}`\n' \
                                 f' - URL: `{api.url}`\n' \
                                 f' - Token: `{api.token}`\n' \
                                 f' - Superuser: `{"Yes" if api.superuser else "No"}`\n\n'

        update.message.reply_text(response_text, parse_mode=ParseMode.MARKDOWN)

        return StartState.CHOICE_ROOT

    def _config_done_choice(self, bot, update):
        """
        Finishes configuration process.
        """
        update.message.reply_text("Configuration completed!")

        return ConversationHandler.END

    def add_start_command(self):
        """
        Setup the bot
        """
        # Start command
        self.dispatcher.add_handler(ConversationHandler(
            entry_points=[CommandHandler('start', self.start)],
            states={
                StartState.CHOICE_ROOT: [
                    RegexHandler(f'^{StartOptions.ADD_API.value}$', self._add_api_choice),
                    RegexHandler(f'^{StartOptions.REMOVE_API.value}$', self._remove_api_choice),
                    RegexHandler(f'^{StartOptions.CURRENT_CONFIG.value}$', self._current_config_choice),
                ],
                StartState.CHOICE_ADD_API: [
                    RegexHandler(f'^{StartOptions.URL.value}$', self._add_api_choice_url),
                    RegexHandler(f'^{StartOptions.NAME.value}$', self._add_api_choice_name),
                    RegexHandler(f'^{StartOptions.USERNAME.value}$', self._add_api_choice_username),
                    RegexHandler(f'^{StartOptions.PASSWORD.value}$', self._add_api_choice_password),
                    RegexHandler(f'^{StartOptions.WALLET.value}$', self._add_api_choice_wallet),
                    RegexHandler(f'^{StartOptions.SUPERUSER.value}$', self._add_api_choice_superuser),
                    RegexHandler(f'^{StartOptions.CURRENT_CONFIG.value}$', self._add_api_choice_current_changes),
                    RegexHandler(f'^{StartOptions.DONE.value}$', self._add_api_config_done),
                ],
                StartState.CHOICE_REMOVE_API: [
                    RegexHandler(f'^{StartOptions.DONE.value}$', self.start),
                    MessageHandler(Filters.text, self._remove_api_config),
                ],
                StartState.CHOICE_URL: [
                    MessageHandler(Filters.text, self._add_api_config_url)
                ],
                StartState.CHOICE_NAME: [
                    MessageHandler(Filters.text, self._add_api_config_name)
                ],
                StartState.CHOICE_USERNAME: [
                    MessageHandler(Filters.text, self._add_api_config_username)
                ],
                StartState.CHOICE_PASSWORD: [
                    MessageHandler(Filters.text, self._add_api_config_password)
                ],
                StartState.CHOICE_WALLET: [
                    MessageHandler(Filters.text, self._add_api_config_wallet)
                ],
                StartState.CHOICE_SUPERUSER: [
                    MessageHandler(Filters.text, self._add_api_config_superuser)
                ]
            },
            fallbacks=[RegexHandler(f'^{StartOptions.FINISH.value}$', self._config_done_choice)]
        ))



