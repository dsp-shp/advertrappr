from contextlib import contextmanager
import duckdb
import os
import typing as t


CREATE: t.Callable = lambda table: 'CREATE OR REPLACE TABLE %(t)s (%(s)s);' % {
    't': table,
    's': ', '.join([k + ' ' + v for k,v in MODELS.get(table).items()]),
}
MODELS: [str, dict[str, str]] = {
    'advs': {
        'processed': "timestamp",
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
        'processed': "timestamp",
        'level': 'varchar',
        'func': 'varchar',
        'text': 'varchar',
        'args': 'varchar',
    },
}
PATH: str = os.path.join(os.path.expanduser('~'), '.advertrappr', 'duck.db')

@contextmanager
def connect() -> t.Generator[None, duckdb.DuckDBPyConnection, None]:
    con = duckdb.connect(PATH)
    try:
        yield con
    finally:
        con.close() 
