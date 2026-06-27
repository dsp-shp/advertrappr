from datetime import datetime
from urllib.parse import urlparse
import click
import json
import time
import typing as t
import sys

import pandas as pd

from advertrappr.settings import settings
from advertrappr.utils import Advert, get_service, send_messages
from advertrappr.utils.logger import getLogger


logger = getLogger(__name__)


@click.group()
@click.pass_context
def cli(ctx: click.Context) -> None:
    ctx.obj = settings


@cli.command()
@click.option('-d', '--dispose', type=int, default=7,
    help='Data dispose (days, default=7, None for no dispose)')
@click.option('-r', '--repeat', type=int, default=None,
    help='Sleep before next search (secs, default=None, None for no repeat)')
@click.argument("urls", help='List of URLs to scrape', nargs=-1)
@click.pass_context
def run(
    ctx: click.Context,
    dispose: t.Optional[int],
    repeat: t.Optional[int],
    urls: tuple[str]
) -> None:
    """Run advertrappr"""
    from advertrappr.utils.logger import addDBHandler

    services: dict[str, str] = {
        x: (urlparse(x).netloc.split('.')[-2]).capitalize() for x in urls
    }

    if not services:
        logger.error('No URL was provided')
        return

    addDBHandler()

    while True:
        advs_stored: pd.DataFrame = pd.DataFrame(columns=['service', 'id'])
        result = settings.db_conn.sql('SELECT DISTINCT service, id FROM advs').fetchdf()
        if not result.empty:
            advs_stored = result
        logger.info('Adverts stored: %s', advs_stored.shape[0])

        advs: list[Advert] = list()
        for url, service_name in services.items():
            try:
                parsed = get_service(service_name).parse(url, **{
                    **settings['scrapper'],
                    **settings['parsers'].get(service_name, {}),
                })
                stored = set(advs_stored.query(
                    'service == "%s"' % service_name
                ).id)
                advs += [x for x in parsed if str(x.id) not in stored]
            except KeyError:
                logger.error('Missing service module: %s', service_name)
            except Exception as e:
                logger.error(e)

        logger.info('New adverts selected: %s', len(advs))
        if advs:
            df = pd.DataFrame(advs)
            df['__processed'] = datetime.now()
            settings.db_conn.sql('INSERT INTO advs SELECT * FROM df')
            send_messages(advs, **settings['messenger'])

        if not repeat:
            return
        time.sleep(repeat)


@cli.command()
@click.argument('query', required=True)
@click.option('-t', '--table', type=bool, default=False, is_flag=True,
    help='Output in table form')
@click.pass_context
def fetch(ctx: click.Context, query: str, table: bool = False) -> None:
    """Fetch any data or execute any query in database"""

    fetched = (settings.db_conn.table if table else settings.db_conn.sql)(query)
    try:
        if len(fetched) == 0:
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
    send_messages(message, **settings['messenger'])


if __name__ in ('__main__'):
    sys.exit(cli())
