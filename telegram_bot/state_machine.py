from enum import Enum

from telegram import ParseMode
from transitions import Machine

__all__ = ['StatusState', 'StatusStateMachine']


class StatusState(Enum):
    ACTIVE = 'active'
    INACTIVE = 'inactive'


class StatusStateMachine(Machine):
    states = [StatusState.INACTIVE.name, StatusState.ACTIVE.name]
    initial = StatusState.INACTIVE.name
    transitions = [
        {'trigger': 'start', 'source': StatusState.INACTIVE.name, 'dest': StatusState.ACTIVE.name, 'after': 'notify_start'},
        {'trigger': 'start', 'source': StatusState.ACTIVE.name, 'dest': StatusState.ACTIVE.name},
        {'trigger': 'stop', 'source': StatusState.INACTIVE.name, 'dest': StatusState.INACTIVE.name},
        {'trigger': 'stop', 'source': StatusState.ACTIVE.name, 'dest': StatusState.INACTIVE.name, 'after': 'notify_stop'},
    ]

    def __init__(self, service):
        super().__init__(self, states=self.states, initial=self.initial, transitions=self.transitions)
        self.service = service

    def notify_start(self, bot, chat):
        bot.send_message(chat_id=chat, text=f'Service `{self.service}` is active and running now',
                         parse_mode=ParseMode.MARKDOWN)

    def notify_stop(self, bot, chat):
        bot.send_message(chat_id=chat, text=f'Service `{self.service}` stops working and is now inactive',
                         parse_mode=ParseMode.MARKDOWN)

    def __str__(self):
        return self.model.state

    def __repr__(self):
        return f'StatusStateMachine{{{self.service}, {self.model.state}}}'
