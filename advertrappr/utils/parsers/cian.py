from ..service import Service
from bs4 import BeautifulSoup

class Cian(Service):
    name: str = 'cian'
    url: str = 'https://cian.ru'
    
    @staticmethod
    def parse(soup: BeautifulSoup, limit: int = 10) -> list[dict]:
        pass
