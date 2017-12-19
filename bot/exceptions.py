from telegram.error import TelegramError


class RequestException(TelegramError):
    def __init__(self, message, url=None, response=None):
        super().__init__(message)
        self.response = response


class NanopoolRequestException(RequestException):
    pass


class EtherscanRequestException(RequestException):
    pass


class BarreneroRequestException(RequestException):
    pass


class ImproperlyConfigured(TelegramError):
    pass


class NoDatabase(Exception):
    pass
