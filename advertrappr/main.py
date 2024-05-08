from .utils import getLogger, parsers, connect, Bot
from datetime import datetime
import click
import json
import os
import pandas as pd
import re
import sys
import typing as t


logger = getLogger(__name__)
 
@click.group()
@click.pass_context
def cli(ctx: click.Context) -> None:
    pass

@cli.command()
@click.option('-a', '--avito-url', type=t.Union[str, None], default=None, 
    help='Avito search URL')
@click.option('-c', '--cian-url', type=t.Union[str, None], default=None, 
    help='Cian search URL')
@click.option('-y', '--yandex-url', type=t.Union[str, None], default=None, 
    help='Yandex search URL')
@click.option('-d', '--dispose', type=t.Union[int, None], default=7,
    help='Data dispose depth (days, default=7, None for no dispose)')
@click.option('-r', '--repeat', type=t.Union[int|None], default=None,
    help='Time to sleep before next search (secs, default=None for no repeat)')
@click.pass_context
def run(
    ctx: click.Context,
    avito_url: str | None = None,
    cian_url: str | None = None,
    yandex_url: str | None = None,
    dispose: int | None = 7,
    repeat: int | None = None
) -> None:
    """ Run advertrappr """
    pass

@cli.command()
@click.argument('query', required=True)
@click.pass_context
def fetch(ctx: click.Context, query: str) -> None:
    """ Execute any query in the database """
    res: pd.DataFrame | None = None
    with connect(read_only=True) as con:
        res = con.execute(query).fetchdf()
    if not res.empty:
        logger.info(json.dumps(res.to_dict("records"), indent=4))

@cli.command()
@click.argument('message', required=True)
@click.pass_context
def send(ctx: click.Context, message: str) -> None:
    """ Send any text message """

    bot = Bot('7036581192:AAHp36vhVhhlzmv1cFPQVpRKm1SvSBXbSzI', '-1002035272908')
    bot.send_message(message)


if __name__ in ('__main__'):
    sys.exit(cli)
