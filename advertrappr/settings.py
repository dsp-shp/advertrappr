from pathlib import Path
import typing as t


BASE_DIR = Path.home() / '.cache' / 'advertrappr'
TEMPLATES_DIR = BASE_DIR / 'templates'
CONFIG_PATH = BASE_DIR / 'config.yaml'
DATABASE_PATH = BASE_DIR / 'duck.db'

MODELS: dict[str, dict[str, str]] = {
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

getCreateSQL = lambda table: 'CREATE TABLE IF NOT EXISTS %(t)s (%(d)s);' % {
    't': table,
    'd': ', '.join([f'{k} {v}' for k, v in {
        **MODELS.get(table, {}),
        '__processed': 'timestamp default now()',
    }.items()]),
}

DEFAULT_CONFIG: dict[str, dict[str, t.Any]] = {
    'connector': {'database': str(DATABASE_PATH)},
    'messenger': {'cooldown': 5, 'disable_web_page_preview': True, 'parse_mode': 'HTML'},
    'scrapper': {'options': ['--disable-gpu', '--no-sandbox', '--headless']},
    'parsers': {},
}
