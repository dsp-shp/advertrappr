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

__fields: [str, str] = {
    '__processed': 'timestamp',
}
""" Технические поля: заполнение полей лежит на стороне СУБД """

PATH: str = os.path.join(os.path.expanduser('~'), '.advertrappr')

create_table: t.Callable = lambda table: 'CREATE OR REPLACE TABLE %(t)s (%(s)s);' % {
    't': table,
    's': ', '.join([k + ' ' + v for k,v in {**__fields, **MODELS.get(table)}.items()]),
}
""" Шорткат для создания таблицы """

@contextmanager
def connect(**kwargs) -> t.Generator[None, duckdb.DuckDBPyConnection, None]:
    con = duckdb.connect(os.path.join(PATH, 'duck.db'), **kwargs)
    try:
        yield con
    finally:
        con.close() 
