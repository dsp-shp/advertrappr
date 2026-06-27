from contextlib import contextmanager
from pathlib import Path
import duckdb
import typing as t


class Settings:
    base_dir = Path.home() / '.cache' / 'advertrappr'
    templates_dir = base_dir / 'templates'
    config_path = base_dir / 'config.yaml'
    database_path = base_dir / 'duck.db'

    adv_columns = [
        'service', 'id', 'title', 'location', 'station',
        'price', 'description', 'link',
    ]

    log_columns = [
        'level', 'func', 'text', 'args',
    ]

    create_advs_table = """CREATE TABLE IF NOT EXISTS advs (
        service varchar,
        id varchar,
        title varchar,
        location varchar,
        station varchar,
        price varchar,
        description varchar,
        link varchar,
        __processed timestamp default now()
    );"""

    create_logs_table = """CREATE TABLE IF NOT EXISTS logs (
        level varchar,
        func varchar,
        text varchar,
        args varchar,
        __processed timestamp default now()
    );"""

    create_tables: dict[str, str] = {
        'advs': create_advs_table,
        'logs': create_logs_table,
    }

    default_config: dict[str, dict[str, t.Any]] = {
        'connector': {'database': str(database_path)},
        'messenger': {
            'cooldown': 5,
            'disable_web_page_preview': True,
            'parse_mode': 'HTML',
        },
        'scrapper': {
            'options': ['--disable-gpu', '--no-sandbox', '--headless'],
        },
        'parsers': {},
    }

    @staticmethod
    @contextmanager
    def connect(
        database: str | None = None,
        read_only: bool = False,
        **kwargs
    ):
        conn = duckdb.connect(
            database or str(Settings.database_path),
            read_only=read_only,
        )
        try:
            yield conn
        finally:
            conn.close()


settings = Settings()
