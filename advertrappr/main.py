from .utils import Advert, connect, getLogger, getService, send_messages
from datetime import datetime
from time import sleep
from yaml import dump, safe_load
import click
import json
import os
import pandas as pd
import re
import sys
import typing as t


PATH: str = os.path.join(os.path.expanduser('~'), '.advertrappr')
CONFIG_PATH: str = os.path.join(PATH, 'config.yaml')
logger = getLogger(__name__)
 
@click.group()
@click.pass_context
def cli(ctx: click.Context) -> None:
    """

    Function reads or generates (templated) config file, creates necessary entities 
    and updates job execution context.

    """
    from .utils.connector import getCreateSQL, MODELS

    basic_config: dict[str, dict[str, t.Any]] = {
        'connector': {'database': os.path.join(PATH, 'duck.db')},
        'messenger': {},
        'scrapper': {'options': ['--disable-gpu', '--no-sandbox', '--headless']},
        'parsers': {},
    }
    config: dict[str, dict[str, t.Any]] | None = None
    
    os.makedirs(PATH, exist_ok=True)
    if not os.path.exists(CONFIG_PATH):
        logger.warning('Конфигурационный "%s" отсутствует или пуст' % CONFIG_PATH)
        with open(CONFIG_PATH, 'w') as f:
            dump(basic_config, f, default_flow_style=False, allow_unicode=True)
        logger.info('Записана базовая конфигурация')
    
    with open(CONFIG_PATH, 'r') as f:
        config = safe_load(f.read())
    if config.get('connector') and 'read_only' in config['connector']: ### параметр определяется вручную
        config['connector'].pop('read_only')
    ctx.obj = {**{x:{} for x in basic_config}, **config}

    with connect(**ctx.obj['connector']) as con:
        existing: set[str] = set(con.sql('SHOW TABLES').fetchdf().name)
        for x in set(MODELS).difference(existing):
            logger.warning('Не найдена рабочая таблица "%s"' % x)
            con.sql(getCreateSQL(x))
            logger.info('Таблица "%s" создана' % x)

@cli.command()
@click.option('-c', '--connector', type=str, default=None,
    help='Database-related string configuration dump')
@click.option('-m', '--messenger', type=str, default=None,
    help='Telegram-related string configuration dump')
@click.option('-s', '--scrapper', type=str, default=None,
    help='Website scrapping string configuration dump')
@click.option('-p', '--parsers', type=str, default=None,
    help='Source code parsing string configuration dump')
@click.pass_context
def config(
    ctx: click.Context,
    connector: str | None = None,
    messenger: str | None = None,
    scrapper: str | None = None,
    parsers: str | None = None
) -> None:
    """ Configuration update """
    from copy import deepcopy

    new_config: dict[str, dict] = {
        'connector': {} if str(connector).strip() in ('None', '',) else json.loads(connector),
        'messenger': {} if str(messenger).strip() in ('None', '',) else json.loads(messenger),
        'scrapper': {} if str(scrapper).strip() in ('None', '',) else json.loads(scrapper),
        'parsers': {} if str(parsers).strip() in ('None', '',) else json.loads(parsers),
    }

    if not any([k for k,v in new_config.items() if v]):
        logger.info('Конфигурация не нуждается в обновлении: пустая конфигурация')
        return

    with open(CONFIG_PATH, 'r') as f:
        config = safe_load(f.read())
    config_copy = deepcopy(config)

    for k,v in new_config.items():
        if not v or config.get(k, {}) == v:
            continue
        config[k] = v
        logger.info('Обновлена конфигурация для "%s": %s' % (k, str(v)))
    
    if config_copy == config:
        logger.info('Конфигурация не нуждается в обновлении: идентичная конфигурация')
        return
    
    with open(CONFIG_PATH, 'w') as f:
        dump(config, f, default_flow_style=False, allow_unicode=True)
    
@cli.command()
@click.option('-a', '--avito-url', type=str, default=None, 
    help='Avito search URL')
@click.option('-c', '--cian-url', type=str, default=None, 
    help='Cian search URL')
@click.option('-y', '--yandex-url', type=str, default=None, 
    help='Yandex search URL')
@click.option('-d', '--dispose', type=int, default=7,
    help='Data dispose (days, default=7, None for no dispose)')
@click.option('-r', '--repeat', type=int, default=None,
    help='Sleep before next search (secs, default=None, None for no repeat)')
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
    from .utils.logger import updateLoggers

    dispose: int | None = int(dispose) if str(dispose) != 'None' else None
    repeat: int | None = int(repeat) if str(repeat) != 'None' else None
    services: dict[str, str] = {
        k.replace('_url', '').capitalize():v for k,v in locals().items() if (
            v and k.endswith('_url')
        )
    } ### наименование параметра без 'url' подстроки и с заглавной
    
    if not services:
        logger.error('Не был предоставлен ни один запрос')
        return

    updateLoggers(log_to_db=True)

    advs_stored: pd.DataFrame = pd.DataFrame(columns=['service', 'id'])
    with connect(read_only=True, **ctx.obj['connector']) as con:
        advs_fetched = con.sql('SELECT DISTINCT service, id FROM advs').fetchdf()
        if not advs_fetched.empty:
            advs_stored = advs_fetched
    logger.info('Объявлений хранится: %s' % advs_stored.shape[0])
     
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
            logger.error('Отсутствует модуль обработки: %s' % name)
        except Exception as e:
            logger.error(e)

    logger.info('Новых объявлений отобрано: %s' % len(advs))
    if advs:
        df = pd.DataFrame(advs)
        df['__processed'] = datetime.now()
        with connect(**ctx.obj['connector']) as con:
            con.sql('INSERT INTO advs SELECT * FROM df')
            send_messages(advs, **ctx.obj['messenger'])
            
    if repeat:
        sleep(repeat)
        run(ctx, avito_url, cian_url, yandex_url, dispose, repeat)
    
@cli.command()
@click.argument('query', required=True)
@click.option('-t', '--table', type=bool, default=False, is_flag=True,
    help='Выборка в табличной форме')
@click.pass_context
def fetch(ctx: click.Context, query: str, table: bool = False) -> None:
    """ Fetch any data or execute any query in database """

    with connect(**ctx.obj['connector']) as con:
        fetched = (con.table if table else con.sql)(query)
        try:
            if len(fetched) == 0:
                logger.info('Пустая выборка')
                return 
        except:
            return
        
        if table == False:
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
    """ Send any text message """
    send_messages(message, **ctx.obj['messenger'])


if __name__ in ('__main__'):
    sys.exit(cli)
