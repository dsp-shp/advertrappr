from bs4 import BeautifulSoup, element
import typing as t
import json
from advertrappr.utils.services.service import Advert, Service, format_string
from advertrappr.utils.logger import getLogger

logger = getLogger(__name__)


class Avito(Service):
    @staticmethod
    def _get_service(x: element.Tag | None = None) -> str:
        return Avito.get_name()

    @staticmethod
    def _get_id(x: element.Tag) -> str:
        return x.get('data-item-id')

    @staticmethod
    def _get_title(x: element.Tag) -> str:
        return x.select("div[class^=iva-item-titleStep-]", limit=1)[0].find('a')

    @staticmethod
    def __get_geo(x: element.Tag) -> element.Tag:
        return x.select("div[class^=geo-root-]", limit=1)[0]

    @staticmethod
    def _get_location(x: element.Tag) -> str:
        return [*Avito.__get_geo(x).children][0]

    @staticmethod
    def _get_station(x: element.Tag) -> str:
        try:
            return [*Avito.__get_geo(x).children][1]
        except:
            return ""

    @staticmethod
    def _get_price(x: element.Tag) -> str:
        return '%s · %s' % (
            format_string(
                x.select("div[class^=iva-item-priceStep-]", limit=1)[0]
            ),
            format_string(
                x.select("div[class^=iva-item-autoParamsStep-]", limit=1)[0]
            )
        )

    @staticmethod
    def _get_description(x: element.Tag) -> str:
        return x.select("div[class^=iva-item-bottomBlock-]", limit=1)[0].find("p")

    @staticmethod
    def _get_link(x: element.Tag) -> str:
        return Avito.get_link() + format_string(x.find('a').get('href'))
    
    @staticmethod
    def _get_images(x: element.Tag) -> str:
        ul: element.Tag = x.select("ul[class^=photo-slider-list-]", limit=1)[0]
        return json.dumps(
            [x.get('data-marker', '').replace('slider-image/image-', '').split('?')[0] for x in ul.children]
        )

    @staticmethod
    def scrape(link: str, *args, **kwargs) -> BeautifulSoup:
        logger.info('Starting scraping')
        return Service.scrape(link, *args, **kwargs)

    @staticmethod
    def parse(link_or_soup: str | BeautifulSoup, limit: int = 10, **kwargs) -> list[Advert]:
        if isinstance(link_or_soup, str):
            soup = Avito.scrape(link_or_soup, **kwargs)
        elif isinstance(link_or_soup, BeautifulSoup):
            soup = link_or_soup
        else:
            raise Exception('URL or BeautifulSoup required')

        tags = [x for x in soup.select(
            "div[class^=iva-item-root-]"
        ) if not x.select("div[class*=iva-item-grow-]")][:limit][::-1]
        logger.info(f"Found {len(tags)} tags from {limit}")
        
        return Service.parse(
            tags,
            {k.split('_', 2)[-1]: v for k, v in vars(Avito).items() if k.startswith('_get_')}
        )
