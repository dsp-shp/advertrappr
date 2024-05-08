from . import getLogger
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

FLAGS: tuple[str] = ('--disable-gpu', '--no-sandbox', '--headless',)
OPTIONS: Options = Options()
for x in FLAGS:
    OPTIONS.add_argument(x)

logger = getLogger(__name__)

def scrape(link: str, handle_captcha: bool = False) -> BeautifulSoup:
    driver: webdriver.Chrome | None = None
    try:
        driver = webdriver.Chrome(options=OPTIONS)
        driver.get(link)
        
        source: str = driver.page_source
        logger.info('Размер исходного кода: %s' % len(source))

        return BeautifulSoup(source, 'html.parser') ### TODO: handle captcha 
    except Exception as e:
        logger.error(e)
        return []
    finally:
        if driver:
            driver.quit()
