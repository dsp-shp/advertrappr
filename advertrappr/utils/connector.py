from contextlib import contextmanager
from collections import namedtuple
import duckdb
import os
import typing as t


MODELS: [str, dict[str, str]] = {
    'advs': {
        'service': 'varchar',
        'id': 'varchar',
        'title': 'varchar',
        'location': 'varchar',
        'station': 'varchar',
        'price': 'varchar',
        'description': 'varchar',
        'link': 'varchar',
    },
    'logs': {
        'level': 'varchar',
        'func': 'varchar',
        'text': 'varchar',
        'args': 'varchar',
    },
}

getCreateSQL: t.Callable = lambda table: 'CREATE TABLE IF NOT EXISTS %(t)s (%(d)s);' % {
    't': table,
    'd': ', '.join([k + ' ' + v for k,v in {
        **MODELS.get(table),
        ### Далее следуют технические поля, автоматически заполняемые на стороне СУБД
        '__processed': 'timestamp default now()', 
    }.items()]),
}

class connect(duckdb.DuckDBPyConnection):
    def __new__(
        cls, 
        database: str = os.path.join(os.path.expanduser('~'), '.advertrappr', 'duck.db'),
        read_only: bool = False,
        **kwargs
    ) -> duckdb.DuckDBPyConnection:
        return duckdb.connect(database=database, read_only=read_only)
