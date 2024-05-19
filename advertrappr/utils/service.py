from .connector import MODELS
from .logger import getLogger
from abc import ABC, abstractmethod
from bs4 import BeautifulSoup, element
from collections import namedtuple
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import typing as t

Advert: type = namedtuple(
    'Advert', MODELS.get('advs').keys(), defaults=(None,) * len(MODELS.get('advs')) 
)

OPTIONS: Options = Options()

logger = getLogger(__name__)

class Service(ABC):
    @staticmethod
    @abstractmethod
    def parse(
        tags: list[element.Tag],
        attrs: dict[str, t.Callable],
        **kwargs
    ) -> list[Advert]:
        """ Парсинг записей из исходного кода """
        advs = [Advert(**{k:v(x) for k,v in attrs.items()}) for x in tags]

        advs_invalid = [x for x in advs if not x.id]
        if advs_invalid:
            logger.error('Ошибки парсинга: %s' % len(advs_invalid))
        
        return advs

    @staticmethod
    @abstractmethod
    def scrape(
        link: str, 
        handle_captcha: bool = False,
        options: list[str] = ['--disable-gpu', '--no-sandbox', '--headless'],
        **kwargs
    ) -> BeautifulSoup:
        """ Базовый скраппинг """
        for x in options:
            OPTIONS.add_argument(x)
        
        driver: webdriver.Chrome | None = None
        try:
            driver = webdriver.Chrome(options=OPTIONS)
            driver.get(link)
            
            source: str = driver.page_source
            logger.info('Размер исходного кода: %s' % len(source))

            return BeautifulSoup(source, 'html.parser')
        except Exception as e:
            logger.error(e)
        finally:
            if driver:
                driver.quit()


def getService(service: str, **kwargs) -> Service:
    from . import services

    service_cls = vars(services).get(service)
    if not service_cls:
        raise Exception('Не обнаружен сервисный модуль для %s' % service)
    return service_cls(**kwargs)
