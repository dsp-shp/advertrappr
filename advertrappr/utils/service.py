from abc import ABC, abstractmethod
from bs4 import BeautifulSoup, element
from collections import namedtuple
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import os
import typing as t

from advertrappr.settings import Settings
from advertrappr.utils.logger import getLogger


Advert: type = namedtuple(
    'Advert', Settings.adv_columns, defaults=(None,) * len(Settings.adv_columns)
)

OPTIONS: Options = Options()

logger = getLogger(__name__)


def format_string(str_or_tag: str | element.Tag, *args, **kwargs) -> str | None:
    if isinstance(str_or_tag, str):
        _ = str_or_tag
    else:
        _ = str_or_tag.text
    return _.replace('\xa0', ' ').strip()


def ensure_format(func: t.Callable) -> t.Callable:
    def _ensure_format(*args, **kwargs) -> str | None:
        try:
            return format_string(func(*args, **kwargs))
        except Exception as e:
            logger.error('Parsing error "%s": %s', func.__name__, e)
    return _ensure_format


class Service(ABC):

    @staticmethod
    @abstractmethod
    def _get_service(x: element.Tag | None = None) -> str:
        pass

    @staticmethod
    @abstractmethod
    def _get_id(x: element.Tag) -> str:
        pass

    @staticmethod
    @abstractmethod
    def _get_title(x: element.Tag) -> str:
        pass

    @staticmethod
    @abstractmethod
    def _get_location(x: element.Tag) -> str:
        pass

    @staticmethod
    @abstractmethod
    def _get_station(x: element.Tag) -> str:
        pass

    @staticmethod
    @abstractmethod
    def _get_price(x: element.Tag) -> str:
        pass

    @staticmethod
    @abstractmethod
    def _get_description(x: element.Tag) -> str:
        pass

    @staticmethod
    @abstractmethod
    def _get_link(x: element.Tag) -> str:
        pass

    @staticmethod
    @abstractmethod
    def scrape(
        link: str,
        handle_captcha: bool = False,
        kill_chrome: bool = True,
        options: list[str] = ['--disable-gpu', '--no-sandbox', '--headless'],
        **kwargs
    ) -> BeautifulSoup:
        for x in options:
            OPTIONS.add_argument(x)

        driver: webdriver.Chrome | None = None
        try:
            driver = webdriver.Chrome(options=OPTIONS)
            driver.get(link)

            source: str = driver.page_source
            logger.info('Page source size: %s', len(source))

            return BeautifulSoup(source, 'html.parser')
        except Exception as e:
            logger.error(e)
        finally:
            if driver:
                driver.quit()
            if kill_chrome:
                os.system('pkill chrome')

    @staticmethod
    @abstractmethod
    def parse(
        tags: list[element.Tag],
        attrs: dict[str, t.Callable],
        **kwargs
    ) -> list[Advert]:
        advs = [Advert(**{k: ensure_format(v)(x) for k, v in attrs.items()}) for x in tags]

        advs_invalid = [x for x in advs if not x.id]
        if advs_invalid:
            logger.error('Parsing errors: %s', len(advs_invalid))

        return advs


def getService(service: str, **kwargs) -> Service:
    from advertrappr.utils import services

    service_cls = vars(services).get(service)
    if not service_cls:
        raise Exception(f'No service module found for {service}')
    return service_cls(**kwargs)
