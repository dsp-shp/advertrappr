from datetime import datetime
from pathlib import Path
from time import sleep
from yaml import dump, safe_load
import click
import json
import pandas as pd
import sys
import typing as t

from advertrappr.settings import (
    BASE_DIR,
    CONFIG_PATH,
    DEFAULT_CONFIG,
    MODELS,
    TEMPLATES_DIR,
    getCreateSQL,
)
from advertrappr.utils import Advert, connect, getLogger, getService, send_messages
from advertrappr.utils.messenger import TEMPLATES as basic_templates


logger = getLogger(__name__)


@click.group()
@click.pass_context
def cli(ctx: click.Context) -> None:
    """
    Read or generate config file, create necessary entities
    and update job execution context.
    """
    from advertrappr.settings import DATABASE_PATH
    from jinja2 import Environment, FileSystemLoader

    config: dict[str, dict[str, t.Any]] | None = None

    BASE_DIR.mkdir(parents=True, exist_ok=True)
    if not CONFIG_PATH.exists():
        logger.warning('Config "%s" not found or empty', CONFIG_PATH)
        with open(CONFIG_PATH, 'w') as f:
            dump(DEFAULT_CONFIG, f, default_flow_style=False, allow_unicode=True)
        logger.info('Default config written')

    TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
    existing_templates = {p.name for p in TEMPLATES_DIR.iterdir()}
    for name, content in basic_templates.items():
        if f'{name}.md' not in existing_templates:
            logger.warning('Template not found: %s.md', name)
            with open(TEMPLATES_DIR / f'{name}.md', 'w') as f:
                f.write(content)
            logger.info('Default template created')

    with open(CONFIG_PATH, 'r') as f:
        config = safe_load(f.read())
    config = {**{x: {} for x in DEFAULT_CONFIG}, **config}

    if 'read_only' in config['connector']:
        config['connector'].pop('read_only')
    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))
    config['messenger']['templates'] = {
        x: env.get_template(x + '.md') for x in basic_templates
    }
    ctx.obj = config

    with connect(**ctx.obj['connector']) as con:
        existing: set[str] = set(con.sql('SHOW TABLES').fetchdf().name)
        for x in set(MODELS).difference(existing):
            logger.warning('Working table "%s" not found', x)
            con.sql(getCreateSQL(x))
            logger.info('Table "%s" created', x)


@cli.command()
@click.option('-a', '--avito-url', type=str, default=None,
    help='Avito search URL')
@click.option('-c', '--cian-url', type=str, default=None,
    help='Cian search URL')
@click.option('-y', '--yandex-url', type=str, default=None,
    help='Yandex search URL')
@click.option('-d', '--dispose', type=str, default='7',
    help='Data dispose (days, default=7, None for no dispose)')
@click.option('-r', '--repeat', type=str, default=None,
    help='Sleep before next search (secs, default=None, None for no repeat)')
@click.pass_context
def run(
    ctx: click.Context,
    avito_url: str | None = None,
    cian_url: str | None = None,
    yandex_url: str | None = None,
    dispose: str | None = 7,
    repeat: str | None = None
) -> None:
    """Run advertrappr"""
    from advertrappr.utils.logger import addDBHandler

    dispose: int | None = int(dispose) if str(dispose) != 'None' else None
    repeat: int | None = int(repeat) if str(repeat) != 'None' else None
    services: dict[str, str] = {
        k.replace('_url', '').capitalize(): v for k, v in locals().items() if (
            v and k.endswith('_url')
        )
    }

    if not services:
        logger.error('No URL was provided')
        return

    addDBHandler()

    while True:
        advs_stored: pd.DataFrame = pd.DataFrame(columns=['service', 'id'])
        with connect(read_only=True, **ctx.obj['connector']) as con:
            advs_fetched = con.sql('SELECT DISTINCT service, id FROM advs').fetchdf()
            if not advs_fetched.empty:
                advs_stored = advs_fetched
        logger.info('Adverts stored: %s', advs_stored.shape[0])

        advs: list[Advert] = list()
        for name, link in services.items():
            try:
                parsed = getService(name).parse(link, **{
                    **ctx.obj['scrapper'],
                    **ctx.obj['parsers'].get(name, {}),
                })
                stored = set(advs_stored.query('service == "%s"' % name.capitalize()).id)
                advs += [x for x in parsed if str(x.id) not in stored]
            except KeyError:
                logger.error('Missing service module: %s', name)
            except Exception as e:
                logger.error(e)

        logger.info('New adverts selected: %s', len(advs))
        if advs:
            df = pd.DataFrame(advs)
            df['__processed'] = datetime.now()
            with connect(**ctx.obj['connector']) as con:
                con.sql('INSERT INTO advs SELECT * FROM df')
                send_messages(advs, **ctx.obj['messenger'])

        if not repeat:
            return
        sleep(repeat)


@cli.command()
@click.argument('query', required=True)
@click.option('-t', '--table', type=bool, default=False, is_flag=True,
    help='Output in table form')
@click.pass_context
def fetch(ctx: click.Context, query: str, table: bool = False) -> None:
    """Fetch any data or execute any query in database"""

    with connect(**ctx.obj['connector']) as con:
        fetched = (con.table if table else con.sql)(query)
        try:
            if len(fetched) == 0:
                logger.info('Empty result set')
                return
        except:
            return

        if not table:
            fetched = json.dumps(
                fetched.fetchdf().astype(str).to_dict("records"),
                ensure_ascii=False,
                indent=4,
            )
        else:
            fetched = '\n%s' % fetched

    logger.info(fetched)


@cli.command()
@click.argument('message', required=True)
@click.pass_context
def send(ctx: click.Context, message: str) -> None:
    """Send any text message"""
    send_messages(message, **ctx.obj['messenger'])


if __name__ in ('__main__'):
    sys.exit(cli)
