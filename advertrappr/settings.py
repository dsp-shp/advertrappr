from typing import NamedTuple
from pathlib import Path
import typing as t

from yaml import dump, safe_load
import duckdb


class Config(NamedTuple):
    messenger: dict[str, t.Any]
    parsers: dict[str, t.Any]
    scrapper: dict[str, t.Any]


class Settings:
    base_path = Path.home() / '.cache' / 'advertrappr'
    temp_path = Path(__file__).parent / 'templates'
    cache_path = base_path / "cache"
    config_path = base_path / 'config.yaml'
    config: Config
    config_default: dict[str, t.Any] = {
        'messenger': {
            'cooldown': 5,
        },
        'scrapper': {
            'options': ['--disable-gpu', '--no-sandbox', '--headless'],
        },
        'parsers': {},
    }
    db_path = base_path / 'duck.db'
    db_conn: duckdb.DuckDBPyConnection

    def __init__(self):
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.temp_path.mkdir(parents=True, exist_ok=True)

        if not self.config_path.exists():
            self.config_path.write_text(dump(
                self.config_default,
                default_flow_style=False,
                allow_unicode=True,
            ))

        self.config = Config(**{
            **{x: {} for x in self.config_default},
            **safe_load(self.config_path.read_text()),
        })

        self.db_conn = duckdb.connect(str(self.db_path), False)
        from advertrappr.utils import Advert, Log
        for x in (Advert, Log):
            self.db_conn.execute("CREATE TABLE IF NOT EXISTS %s (%s)" % (
                x.__name__.lower()[:3] + "s",
                ' TEXT, '.join([*x.__annotations__.keys(), '__processed TIMESTAMP DEFAULT now()']),
            ))

    def __getitem__(self, key):
        return self.config[key]

    def __setitem__(self, key, value):
        self.config[key] = value


settings = Settings()
