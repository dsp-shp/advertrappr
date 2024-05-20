from ..logger import getLogger
from ..service import Advert, Service, format_string
from bs4 import BeautifulSoup, element
import typing as t


logger = getLogger(__name__)

class Avito(Service):
    name: str = 'Avito'
    link: str = 'https://www.avito.ru'
    
    @staticmethod
    def _get_service(x: element.Tag | None = None) -> str:
        return Avito.name 

    @staticmethod
    def _get_id(x: element.Tag) -> str:
        return x.get('data-item-id')

    @staticmethod
    def _get_title(x: element.Tag) -> str:
        return x.find('div', attrs={'class':'iva-item-titleStep-pdebR'}).find('a')

    @staticmethod
    def _get_location(x: element.Tag) -> str:
        return x.find('div', attrs={'class': 'geo-root-zPwRk'}).find('p')

    @staticmethod
    def _get_station(x: element.Tag) -> str:
        return ', '.join([x for x in map(
            format_string,
            x.find('p', attrs={'class': 'styles-module-root_top-p0_50'}).find_all('span')[1:]
        ) if x])

    @staticmethod
    def _get_price(x: element.Tag) -> str:
        return '%s · %s' % (
            format_string(x.find('div', attrs={'class': 'iva-item-priceStep-uq2CQ'})),
            format_string(x.find('div', attrs={'class': 'iva-item-autoParamsStep-WzfS8'}))
        )

    @staticmethod
    def _get_description(x: element.Tag) -> str:
        return x.find('div', attrs={'class': 'iva-item-descriptionStep-C0ty1'})

    @staticmethod
    def _get_link(x: element.Tag) -> str:
        return Avito.link + format_string(x.find('a').get('href'))

    @staticmethod
    def scrape(link: str, *args, **kwargs) -> BeautifulSoup:
        logger.info('Приступаю к скраппингу')
        return Service.scrape(link, *args, **kwargs)

    @staticmethod
    def parse(link_or_soup: str | BeautifulSoup, limit: int = 10, **kwargs) -> list[Advert]:
        if isinstance(link_or_soup, str):
            soup = Avito.scrape(link_or_soup, **kwargs)
        elif isinstance(link_or_soup, BeautifulSoup):
            soup = link_or_soup
        else:
            raise Exception('Необходима ссылка или суп исходного кода')

        tags = soup.find_all('div', {'class': 'iva-item-root-_lk9K'})[:limit][::-1]
        return Service.parse(
            tags,
            {k.split('_', 2)[-1]:v for k,v in vars(Avito).items() if k.startswith('_get_')}
        )
