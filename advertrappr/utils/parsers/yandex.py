from .service import Service
from bs4 import BeautifulSoup

class Yandex(Service):
    name: str = 'yandex'
    url: str = 'https://realty.ya.ru'
    
    @staticmethod
    def parse(soup: BeautifulSoup, limit: int = 10) -> list[dict]:
        pass
