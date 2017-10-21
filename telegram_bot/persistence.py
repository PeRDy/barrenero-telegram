import logging

import peewee

logger = logging.getLogger(__name__)


DEFAULT_DB_FILE = '.data/barrenero_telegram.db'
db = peewee.SqliteDatabase(DEFAULT_DB_FILE, threadlocals=True)


class BaseModel(peewee.Model):
    class Meta:
        database = db


class Chat(BaseModel):
    id = peewee.IntegerField(verbose_name='id', primary_key=True, help_text='Telegram chat id')
    token = peewee.CharField(verbose_name='API token', help_text='Barrenero API token')
    superuser = peewee.BooleanField(verbose_name='API superuser', help_text='Is a superuser in Barrenero API',
                                    default=False)
    last_transaction = peewee.CharField(verbose_name='last transaction hash', null=True, default=None,
                                        help_text='Last transaction hash')

    def __str__(self):
        return self.id

    def __repr__(self):
        attrs = [self.id, f'token={self.token}']
        if self.last_transaction:
            attrs.append(f'last_transaction={self.last_transaction}')

        if self.superuser:
            attrs.append('superuser')

        return f'Chat{{{", ".join(attrs)}}}'

    def __hash__(self):
        return hash(self.id)


def initialize_db():
    db.connect()
    db.create_tables([Chat], safe=True)
