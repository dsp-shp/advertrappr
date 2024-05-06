from ..connector import Record
from ..logger import getLogger
from ..service import Service
from bs4 import BeautifulSoup


logger = getLogger(__name__)

class Avito(Service):
    name: str = 'avito'
    url: str = 'https://www.avito.ru'

    @staticmethod
    def parse_avito(soup: BeautifulSoup, limit: int = 10) -> list[Record]:
        results = soup.find_all(
                'div', {'class': 'iva-item-root-_lk9K'}
        )[:limit][::-1]

        advs: list[dict] = []
        for x in results:
            try:
                advs.append(Record(
                    service='avito',
                    id=str(x.get('data-item-id')).strip(),
                    title=x.find(
                        'div', attrs={'class':'iva-item-titleStep-pdebR'}
                    ).find('a').text.replace('\xa0', ' '),
                    location=x.find(
                        'div', attrs={'class': 'geo-root-zPwRk'}
                    ).find('p').text.replace('\xa0', ' '),
                    station=', '.join([
                        y.text.replace('\xa0', '') for y in x.find(
                            'p', attrs={'class': 'styles-module-root_top-p0_50'}
                        ).find_all('span')[1:] if y.text
                    ]),
                    price='%s · %s' % (
                        x.find(
                            'div', attrs={'class': 'iva-item-priceStep-uq2CQ'}
                        ).text.replace('\xa0', ' '),
                        x.find(
                            'div', attrs={'class': 'iva-item-autoParamsStep-WzfS8'}
                        ).text.replace('\xa0', ' ')
                    ),
                    description=x.find(
                        'div', attrs={'class': 'iva-item-descriptionStep-C0ty1'}
                    ).text.replace('\xa0', ' '),
                    link=Avito.url + str(x.find('a').get('href'))
                ))
            except Exception as e:
                link_invalid = Avito.url + str(x.find('a').get('href')) 
                advs.append(Record(**{
                    'service': Avito.name, 
                    'link': link_
                }))

        advs_invalid = [x for x in advs if not x.get('id')]
        if advs_invalid:
            logger.error('Ошибки парсинга: %s' % len(advs_invalid))
        return advs
