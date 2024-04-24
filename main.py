from bs4 import BeautifulSoup
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from sqlalchemy import create_engine, Engine
from sqlalchemy.sql import text
###
import os
import argparse
import asyncio
import logging
import pandas as pd
import re
import telegram
import typing as t


OPTIONS: Options = Options()
for x in ('--disable-gpu', '--no-sandbox', '--headless',):
    OPTIONS.add_argument(x)

ENGINE: Engine = create_engine('postgresql+psycopg2://postgres:zz1234@localhost:5432/postgres', isolation_level="AUTOCOMMIT")
with ENGINE.connect() as con:
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

logger = logging.getLogger(__name__)


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
    
    """
    if id:
        text: str = '\n'.join([
            '⠀',
            '*%s: [%s]\\(%s\\)*' % (service.capitalize(), title, link.replace('_', '\\_')),
            '⠀',
            '*%s* [%s]\\(https://2gis.ru/spb/search/Cанкт-Петербург,⠀%s\\)' % (station, location, location.replace(' ', '⠀')),
            '_%s_' % price,
            '⠀\n>%s...' % re.sub(r'\n[\ |\n|\t]*', ' ', description).replace('  ', ' ')[:200],
            '\n⠀'
        ])
    else:
        text: str = '⠀\n*Ошибка парсинга:*  %s\n⠀' % link
    
    ### Экранирование сообщения
    for c in ('.', '-', '+', '(', ')', '!'):
        text = text.replace(c, '\\' + c)
    for c in ('\\\\(', '\\\\)'):
        text = text.replace(c, c[-1])
    
    return text

def parse_avito(soup: BeautifulSoup, url: str = 'https://www.avito.ru') -> list[dict]:
    """ Парсинг объявлений Авито 
    """
    results = soup.find_all('div', {'class': 'iva-item-root-_lk9K'})[:10][::-1] ### выбрать первые 20 и отсортировать от старых к новым
    ads: list[dict] = []
    for x in results:
        try:
            ads.append({
                'service': 'avito',
                'id': x.get('data-item-id'),
                'title': x.find('div', attrs={'class':'iva-item-titleStep-pdebR'}).find('a').text.replace('\xa0', ' '),
                'location': x.find('div', attrs={'class': 'geo-root-zPwRk'}).find('p').text.replace('\xa0', ' '),
                'station':  ', '.join([y.text.replace('\xa0', '') for y in x.find('p', attrs={'class': 'styles-module-root_top-p0_50'}).find_all('span')[1:] if y.text]),
                # 'station': '%s, %s' % (
                #     x.find('div', attrs={'class': 'geo-root-zPwRk'}).find_all('p')[-1].find_all('span')[1].text,
                #     x.find('div', attrs={'class': 'geo-root-zPwRk'}).find_all('p')[-1].find_all('span')[2].text
                # ),
                'price': '%s · %s' % (
                    x.find('div', attrs={'class': 'iva-item-priceStep-uq2CQ'}).text.replace('\xa0', ' '),
                    x.find('div', attrs={'class': 'iva-item-autoParamsStep-WzfS8'}).text.replace('\xa0', ' ')
                ),
                'description': x.find('div', attrs={'class': 'iva-item-descriptionStep-C0ty1'}).text.replace('\xa0', ' '),
                'link': url + str(x.find('a').get('href'))
            })
        except Exception as e:
            ads.append(
                {'service': 'avito', 'link': url + str(x.find('a').get('href'))}
            )
            logger.error('%s (%s)' % (e, x.get('data-item-id')))
    return ads

def parse(service: str, link: str, ads: set = set()) -> list[dict]:
    """ Парсинг данных источника 

    """
    driver = None
    parsed_ads: list[dict] = []
    try:
        driver = webdriver.Chrome(options=OPTIONS)
        driver.get(link)
        source: str = driver.page_source
        ### logging.info('Размер исходного кода: %s' % len(source))
        soup = BeautifulSoup(source, 'html.parser')
        ### logger.info(globals()['parse_%s' % service])
        parsed_ads = globals()['parse_%s' % service](soup)
        return [x for x in parsed_ads if x.get('id') and x.get('id') not in ads]
    except Exception as e:
        logger.error(e)
        return []
    finally:
        if driver:
            driver.quit()

async def main(
    avito_url: str | None = None,
    cian_url: str | None = None,
    retention: int = 7,
    cooldown: int = 90
) -> None:
    """ Основная функция
    
    """
    services: dict[str, str] = {k:v for k,v in locals().items() if k.endswith('_url') and v}
    
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
        with ENGINE.connect() as con:
            ### Выбрать уже имеющиеся в базе данных объявления
            df: pd.DataFrame = pd.read_sql_table('ads', con=con)
        ads: list[dict] = []
        dms: list[dict] = []
        for service, link in services.items():
            ads += parse(service, link, {*df[df.service==service].id})
       
        if not ads:
            await asyncio.sleep(cooldown)
            continue 
        
        ### Сохранить данные
        with ENGINE.connect() as con:
            pd.DataFrame(ads).to_sql('ads', con=con, if_exists='append', index=False)
        
        for x in ads:
            error: str | None = None
            async with BOT:
                try:
                    await BOT.send_message(
                        text=prepare(**x), parse_mode='MarkdownV2', chat_id=CHAT_ID, disable_web_page_preview=True
                    ) # type: ignore
                except Exception as e:
                    error = str(e)
                finally:
                    x['error'] = error
                    dms.append(x)
                    await asyncio.sleep(5)
        
        ### Залогировать отправку
        with ENGINE.connect() as con:
            pd.DataFrame(dms)[['service', 'id', 'link', 'error']].to_sql('dms', con=con, if_exists='append', index=False)

        await asyncio.sleep(cooldown)


if __name__ in ('__main__'):
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    logging.info('Идентификатор процесса: %s' % os.getpid())
    parser = argparse.ArgumentParser()
    parser.add_argument('-a', '--avito-url', help='Avito URL', type=str)
    parser.add_argument('-c', '--cian-url', help='Cian URL', type=str)
    parser.add_argument('--token', help='Telegram bot token', type=str)
    parser.add_argument('--chat-id', help='Telegram chat ID', type=str)
    parser.add_argument('--retention', help='Data retention depth', type=int)
    parser.add_argument('--cooldown', help='Time for script in seconds to sleep before next search', type=int)
    args: dict[str, str] = {k:v for k,v in vars(parser.parse_args()).items() if v}
    
    BOT = telegram.Bot(token=args.pop('token'))
    CHAT_ID = args.pop('chat_id')

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(**args))
