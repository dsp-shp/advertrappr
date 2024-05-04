from .utils import getLogger, parsers
from datetime import datetime
import asyncio
import os
import pandas as pd
import re
import sys
import typing as t


# logger = logging.getLogger(__name__)

def prepare(
    service: str,
    id: str,
    title: str,
    location: str,
    station: str,
    price: str,
    description: str,
    link: str,
    **kwargs
) -> str:
    """ Подготовка сообщения
    
    Идентификатор объявления `id` здесь является маркером корректности парсинга
    объявления: в случае если `id` отсутствует, можно считать, что объявление
    обработанно некорректно.

    """
    if id:
        service_capt = service.capitalize()
        link_repl = link.replace('_', '\\_')
        location_repl = location.replace(' ', '⠀')
        description_repl = re.sub(
            r'\n[\ |\n|\t]*', ' ', description
        ).replace('  ', ' ')[:200]
        text = MSG_TMP % locals()
    else:
        text = '⠀\n*Ошибка парсинга:*  %s\n⠀' % link
    
    ### Экранирование сообщения
    for c in ('.', '-', '+', '(', ')', '!'):
        text = text.replace(c, '\\' + c)
    for c in ('\\\\(', '\\\\)'):
        text = text.replace(c, c[-1])
    
    return text

def parse(service: str, link: str, ads: set = set()) -> list[dict]:
    """ Парсинг данных источника 

    """
    driver = None

    parsed_ads: list[dict] = []
    try:
        driver = webdriver.Chrome(options=OPTIONS)
        driver.get(link)
        source: str = driver.page_source
        logger.debug('Размер исходного кода страницы: %s' % len(source))

        soup = BeautifulSoup(source, 'html.parser')
        parsed_ads = vars(parsers).get(service).parse(soup)
        logger.info('Ошибок парсинга: %s' % len([x for x in parsed_ads if not x.get('id')]))

        new_ads = [x for x in parsed_ads if x.get('id') and x.get('id') not in ads]
        logger.info('Найдено новых объявлений: %s' % len(new_ads))

        return new_ads
    except Exception as e:
        logger.error(e)
        return []
    finally:
        if driver:
            driver.quit()

async def main(
    avito_url: str | None = None,
    cian_url: str | None = None,
	yandex_url: str | None = None,
    retention: int = 7,
    cooldown: int = 90
) -> None:
    services: dict[str, str] = {
        k.replace('_url', ''):v for k,v in locals().items() if v and '_url' in k
    } ### корректировка для удаления '_url' подстроки из названия сервиса
    
    os.system('pkill chrome') ### завершить все неактуальные процессы
    ### Если не предоставлен ни один запрос
    if not services:
        logger.error('Не предоставлен ни один запрос...')
        return

    with ENGINE.connect() as con:
        ### Data retention
        con.execute(text("""
            delete from ads 
            where processed::date < now()::date - %(r)s;
            delete from dms 
            where processed::date < now()::date - %(r)s;
        """ % {'r': retention}))

    while True:
        df: pd.DataFrame = pd.DataFrame()
        with ENGINE.connect() as con:
            ### Выбрать уже имеющиеся в базе данных объявления
            df = pd.read_sql_table('ads', con=con)
        ads: list[dict] = []
        dms: list[dict] = []
        stored_ads: set[str] = set()
        for service, link in services.items():
            stored_ads = {x.strip() for x in df[df.service == service].id if x}
            logger.debug('Объявлений хранится: %s' % len(stored_ads))
            ads += parse(service, link, stored_ads)
       
        if not ads:
            await asyncio.sleep(cooldown)
            continue 
        
        ### Сохранить данные
        with ENGINE.connect() as con:
            pd.DataFrame(ads).to_sql(
                'ads', 
                con=con, 
                if_exists='append', 
                index=False
            )
        
        for x in ads:
            error: str | None = None
            async with BOT:
                try:
                    await BOT.send_message(
                        text=prepare(**x), 
                        parse_mode='MarkdownV2', 
                        chat_id=CHAT_ID, 
                        disable_web_page_preview=True
                    ) # type: ignore
                except Exception as e:
                    error = str(e)
                finally:
                    x['error'] = error
                    dms.append(x)
                    await asyncio.sleep(5)
        
        ### Залогировать отправку
        with ENGINE.connect() as con:
            pd.DataFrame(dms)[['service', 'id', 'link', 'error']].to_sql(
                'dms', 
                con=con, 
                if_exists='append', 
                index=False
            )

        await asyncio.sleep(cooldown)

def cli() -> None:
    """ Команда терминала для захвата объявлений

    """
    parser = argparse.ArgumentParser()
    parser.add_argument('-a', '--avito-url', type=str, 
        help='Avito search URL')
    parser.add_argument('-c', '--cian-url', type=str, 
        help='Cian search URL')
    parser.add_argument('--token', type=str, 
        help='Telegram Bot\' token string')
    parser.add_argument('--chat-id', type=str, 
        help='Telegram chat ID')
    parser.add_argument('--con-string', type=str, 
        help='Postgres\' connection URI')
    parser.add_argument('--retention', type=int, default=7, 
        help='Data retention depth (days, default=7)')
    parser.add_argument('--cooldown', type=int, default=90, 
        help='Time to sleep before next search (secs, default=90)')
    parser.add_argument('--log-output', type=str, default='stdout', 
        help='Logging output type, default="stdout"')
    args: dict[str, str] = {k:v for k,v in vars(parser.parse_args()).items() if v}

    ### Инициализация системы логирования
    log_params: dict[str, t.Any] = {
        'level': logging.INFO,
        'format': '%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s',
        'datefmt': '%Y-%m-%d %H:%M:%S'
    }
    log_output: str = args.pop('log_output')
    if log_output == 'file':
        log_dir = os.path.join(os.path.expanduser('~'), '.advertrappr')
        os.makedirs(os.path.join(log_dir), exist_ok=True)
        log_output = os.path.join(log_dir, 'out.log')
        with open(log_output, 'w') as f: f.write('')
        log_params['filename'] = log_output
    elif log_output == 'stdout':
        log_output = log_output.upper()
    else:
        raise Exception('Способ логирования - "%s" неизвестен' % log_output)
    logging.basicConfig(**log_params)
    logging.info('Инициализировано логирование в %s' % log_output)
   
    ### Определение параметров подключения к внешним сервисам
    global BOT, CHAT_ID, CON_STRING, ENGINE 
    BOT = telegram.Bot(token=args.pop('token'))
    CHAT_ID = args.pop('chat_id')
    CON_STRING = args.pop('con_string')
    ENGINE = create_engine(CON_STRING, isolation_level="AUTOCOMMIT")
    
    with ENGINE.connect() as con: ### ициниализация необходимых объектов
        con.execute(text("""
            create table if not exists ads (
                service varchar,
                id varchar,
                title varchar,
                location varchar,
                station varchar,
                price varchar,
                description varchar,
                link varchar,
                processed timestamp default now() + interval '3 hour'
            );

            create table if not exists dms (
                service varchar,
                id varchar,
                link varchar,
                error varchar,
                processed timestamp default now() + interval '3 hour'
            );
        """))

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(**args))

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #



if __name__ in ('__main__'):
    sys.exit()
    #sys.exit(cli())
