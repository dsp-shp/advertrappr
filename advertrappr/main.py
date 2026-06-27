from datetime import datetime
from time import sleep
import click
import json
import pandas as pd
import sys

from advertrappr.settings import Settings, settings
from advertrappr.utils import Advert, getLogger, getService, send_messages
from advertrappr.utils.messenger import TEMPLATES as basic_templates


logger = getLogger(__name__)


@click.group()
@click.pass_context
def cli(ctx: click.Context) -> None:
    ctx.obj = settings


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
        result = settings.conn.sql('SELECT DISTINCT service, id FROM advs').fetchdf()
        if not result.empty:
            advs_stored = result
        logger.info('Adverts stored: %s', advs_stored.shape[0])

        advs: list[Advert] = list()
        for name, link in services.items():
            try:
                parsed = getService(name).parse(link, **{
                    **settings['scrapper'],
                    **settings['parsers'].get(name, {}),
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
            settings.conn.sql('INSERT INTO advs SELECT * FROM df')
            send_messages(advs, **settings['messenger'])

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

    fetched = (settings.conn.table if table else settings.conn.sql)(query)
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

    print(fetched)


@cli.command()
@click.argument('message', required=True)
@click.pass_context
def send(ctx: click.Context, message: str) -> None:
    """Send any text message"""
    send_messages(message, **settings['messenger'])


if __name__ in ('__main__'):
    sys.exit(cli())
