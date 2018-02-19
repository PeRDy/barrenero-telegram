import logging
from configparser import ConfigParser

from telegram import Bot, ParseMode
from telegram.ext import CommandHandler, Updater, messagequeue as mq

from bot.mixins.ether import EtherMixin
from bot.mixins.miner import MinerMixin
from bot.mixins.start import StartMixin
from bot.mixins.storj import StorjMixin
from bot.mixins.wallet import WalletMixin
from bot.models import initialize_db


class MQBot(Bot):
    """A subclass of Bot which delegates send method handling to MQ"""

    def __init__(self, *args, is_queued_def=True, burst_messages=5, burst_time=15000, **kwargs):
        super(MQBot, self).__init__(*args, **kwargs)
        # below 2 attributes should be provided for decorator usage
        self._is_messages_queued_default = is_queued_def
        self._msg_queue = mq.MessageQueue(all_burst_limit=burst_messages, all_time_limit_ms=burst_time)

    def __del__(self):
        try:
            self._msg_queue.stop()
        except:
            pass
        super(MQBot, self).__del__()

    @mq.queuedmessage
    def send_message(self, *args, **kwargs):
        return super(MQBot, self).send_message(*args, **kwargs)


class TelegramBot(StartMixin, MinerMixin, EtherMixin, StorjMixin, WalletMixin):
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
        super().__init__()

        # Read bot config from file
        config_from_file = ConfigParser()
        config_from_file.read(config)
        self._telegram_token = config_from_file.get('telegram', 'token', fallback=None)

        # Initialize DB
        initialize_db()

        self.logger = logging.getLogger('telegram')

        self.updater = Updater(bot=MQBot(self._telegram_token))
        self.dispatcher = self.updater.dispatcher

    def help(self, bot, update):
        """
        Shows help message.
        """
        chat_id = update.message.chat_id
        bot.send_message(chat_id, self.HELP_TEXT, parse_mode=ParseMode.MARKDOWN)

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
        self.add_start_command()

        # Miner command
        self.add_miner_command()

        # Ether command
        self.add_ether_command()
        self.add_ether_jobs()

        # Storj command
        self.add_storj_command()
        self.add_storj_jobs()

        # Wallet command
        self.add_wallet_command()
        self.add_wallet_jobs()

        # Error handler
        self.dispatcher.add_error_handler(self.error)

        try:
            self.updater.start_polling(timeout=30.0)

            self.updater.idle()
        except:
            self.updater.stop()
