import logging

import peewee

logger = logging.getLogger(__name__)


DEFAULT_DB_FILE = 'config/barrenero_telegram.db'
db = peewee.SqliteDatabase(DEFAULT_DB_FILE, threadlocals=True, pragmas=(('foreign_keys', 'on'),))


class BaseModel(peewee.Model):
    class Meta:
        database = db


class Chat(BaseModel):
    id = peewee.IntegerField(verbose_name='id', primary_key=True, help_text='Telegram chat id')
    last_transaction = peewee.CharField(verbose_name='last transaction hash', null=True, default=None,
                                        help_text='Last transaction hash')

    def __str__(self):
        return self.id

    def __repr__(self):
        attrs = [self.id]
        if self.last_transaction:
            attrs.append(f'last_transaction={self.last_transaction}')

        return f'Chat{{{", ".join(attrs)}}}'

    def __hash__(self):
        return hash(self.id)


class API(BaseModel):
    name = peewee.CharField(verbose_name='name', help_text='Barrenero API name')
    url = peewee.CharField(verbose_name='url', help_text='Barrenero API url')
    token = peewee.CharField(verbose_name='API token', help_text='Barrenero API token')
    superuser = peewee.BooleanField(verbose_name='API superuser', help_text='Is a superuser in Barrenero API',
                                    default=False)
    chat = peewee.ForeignKeyField(Chat, related_name='apis')

    def __str__(self):
        return self.id

    def __repr__(self):
        attrs = [self.id, f'token={self.token}']

        if self.superuser:
            attrs.append('superuser')

        return f'API{{{", ".join(attrs)}}}'

    def __hash__(self):
        return hash(self.id)


def initialize_db():
    db.connect()
    db.create_tables([Chat, API], safe=True)
