from . import getLogger, parsers
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


OPTIONS: Options = Options()
for x in ('--disable-gpu', '--no-sandbox', '--headless',):
    OPTIONS.add_argument(x)

logger = getLogger(__name__)

def scrape(link: str, handle_captcha: bool = False) -> list[dict]:
    try:
        driver = webdriver.Chrome(options=OPTIONS)
        driver.get(link)
        source: str = driver.page_source
        logger.debug('Размер исходного кода страницы: %s' % len(source))

        soup = BeautifulSoup(source, 'html.parser') ### TODO: handle captcha 
        return vars(parsers).get(service).parse(soup)
    except Exception as e:
        logger.error(e)
        return []
    finally:
        if driver:
            driver.quit()
