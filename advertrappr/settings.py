from pathlib import Path
from yaml import dump, safe_load
from jinja2 import Environment, FileSystemLoader
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

    def __init__(self):
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.templates_dir.mkdir(parents=True, exist_ok=True)

        if not self.config_path.exists():
            with open(self.config_path, 'w') as f:
                dump(self.default_config, f, default_flow_style=False, allow_unicode=True)

        from advertrappr.utils.messenger import TEMPLATES as basic_templates

        existing = {p.name for p in self.templates_dir.iterdir()}
        for name, content in basic_templates.items():
            if f'{name}.md' not in existing:
                with open(self.templates_dir / f'{name}.md', 'w') as f:
                    f.write(content)

        with open(self.config_path) as f:
            config = safe_load(f.read())
        config = {**{x: {} for x in self.default_config}, **config}
        config['connector'].pop('read_only', None)

        env = Environment(loader=FileSystemLoader(str(self.templates_dir)))
        config['messenger']['templates'] = {
            x: env.get_template(f'{x}.md') for x in basic_templates
        }
        self.config = config

        self.conn = duckdb.connect(
            config['connector'].get('database', str(self.database_path)),
            read_only=False,
        )

        for sql in self.create_tables.values():
            self.conn.execute(sql)

    def __getitem__(self, key):
        return self.config[key]

    def __setitem__(self, key, value):
        self.config[key] = value


settings = Settings()
