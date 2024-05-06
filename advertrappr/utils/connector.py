from contextlib import contextmanager
from collections import namedtuple
import duckdb
import os
import typing as t


CREATE: t.Callable = lambda table: 'CREATE OR REPLACE TABLE %(t)s (%(s)s);' % {
    't': table,
    's': ', '.join([k + ' ' + v for k,v in MODELS.get(table).items()]),
}
MODELS: [str, dict[str, str]] = {
    'advs': {
        '__processed': 'timestamp',
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
        '__processed': 'timestamp',
        'level': 'varchar',
        'func': 'varchar',
        'text': 'varchar',
        'args': 'varchar',
    },
}
PATH: str = os.path.join(os.path.expanduser('~'), '.advertrappr', 'duck.db')
Record: type = namedtuple(
    'Record', 
     {x for x in MODELS.get('advs').keys() if not x.startswith('__')}, 
    ### defaults=(None,) * len(ADVS_COLS)
)

@contextmanager
def connect() -> t.Generator[None, duckdb.DuckDBPyConnection, None]:
    con = duckdb.connect(PATH)
    try:
        yield con
    finally:
        con.close() 
