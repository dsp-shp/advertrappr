from ..logger import getLogger
from ..service import Service, Advert
from bs4 import BeautifulSoup, element
import typing as t


logger = getLogger(__name__)

def _format_string(str_or_tag: str | element.Tag, *args, **kwargs) -> str | None:
    if isinstance(str_or_tag, str):
        _ = str_or_tag
    else:
        _ = str_or_tag.text
    return _.replace('\xa0', ' ').strip()

def ensure_format(func: t.Callable) -> t.Callable:
    def _ensure_format(*args, **kwargs) -> str | None:
        try:
            return _format_string(func(*args, **kwargs))
        except Exception as e:
            logger.error('Ошибка парсинга "%s": %s' % (func.__name__, e)) 
    return _ensure_format

### Функции модуля для парсинга конкретных атрибутов из исходного кода страницы

@ensure_format
def _get_service(*args, **kwargs) -> str:
    return Avito.name 

@ensure_format
def _get_id(x: element.Tag) -> str:
    return x.get('data-item-id')

@ensure_format
def _get_title(x: element.Tag) -> str:
    return x.find('div', attrs={'class':'iva-item-titleStep-pdebR'}).find('a')

@ensure_format
def _get_location(x: element.Tag) -> str:
    return x.find('div', attrs={'class': 'geo-root-zPwRk'}).find('p')

@ensure_format
def _get_station(x: element.Tag) -> str:
    return ', '.join([x for x in map(
        _format_string,
        x.find('p', attrs={'class': 'styles-module-root_top-p0_50'}).find_all('span')[1:]
    ) if x])

@ensure_format
def _get_price(x: element.Tag) -> str:
    return '%s · %s' % (
        _format_string(x.find('div', attrs={'class': 'iva-item-priceStep-uq2CQ'})),
        _format_string(x.find('div', attrs={'class': 'iva-item-autoParamsStep-WzfS8'}))
    )

@ensure_format
def _get_description(x: element.Tag) -> str:
    return x.find('div', attrs={'class': 'iva-item-descriptionStep-C0ty1'})

@ensure_format
def _get_link(x: element.Tag) -> str:
    return Avito.link + _format_string(x.find('a').get('href'))


class Avito(Service):
    name: str = 'Avito'
    link: str = 'https://www.avito.ru'
    
    @staticmethod
    def get_attrs() -> dict[str, t.Callable]:
        return {
            'service': _get_service,
            'id': _get_id,
            'title': _get_title,
            'location': _get_location,
            'station': _get_station,
            'price': _get_price,
            'description': _get_description,
            'link': _get_link,
        }
        #return {k.split('_', 2)[-1]:v for k,v in globals().items() if k.startswith('_get_')}

    @staticmethod
    def scrape(link: str, *args, **kwargs) -> BeautifulSoup:
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
        return Service.parse(tags, Avito.get_attrs())
