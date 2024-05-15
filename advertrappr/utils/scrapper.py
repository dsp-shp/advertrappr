from . import getLogger
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


OPTIONS: Options = Options()

logger = getLogger(__name__)

def scrape(
    link: str, 
    handle_captcha: bool = False,
    options: list[str] = ['--disable-gpu', '--no-sandbox', '--headless'],
) -> BeautifulSoup:
    for x in options:
        OPTIONS.add_argument(x)
    
    driver: webdriver.Chrome | None = None
    try:
        driver = webdriver.Chrome(options=OPTIONS)
        driver.get(link)
        
        source: str = driver.page_source
        logger.info('Размер исходного кода: %s' % len(source))

        return BeautifulSoup(source, 'html.parser') ### TODO: handle captcha 
    except Exception as e:
        logger.error(e)
    finally:
        if driver:
            driver.quit()
