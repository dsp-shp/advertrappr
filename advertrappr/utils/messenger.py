from . import Advert, getLogger
from telegram import Bot as _Bot
from time import sleep
import asyncio
import re
import typing as t


ERROR_MESSAGE: str = '⠀\n\
*Ошибка парсинга:* %(link)s\n⠀'
MESSAGE: str = '⠀\n\
*%(service)s: [%(title)s]\\(%(link)s\\)*\n\
⠀\n\
*%(station)s* [%(location)s]\\(https://2gis.ru/spb/search/%(location_repl)s\\)\n\
\\_%(price)s\\_\n\
⠀\n\
>%(description_repl)s...\n⠀'

logger = getLogger(__name__)

class Bot(_Bot):
    _chat_id: str
    
    def __init__(self, token: str, chat_id: str) -> None:
        super().__init__(token)
        self._chat_id = chat_id

    @property
    def chat_id(self) -> str: 
        return self._chat_id

    @staticmethod
    def format_record(record: Advert | str) -> str:
        _repl: t.Callable = lambda x: re.sub(
            r'\n[\ |\n|\t]*', ' ', x ### заменить все отступы символом пробела, 
        ).replace(' ', '⠀')[:200] ### заменить все пробелы на неразрывные и обрезать
        
        text: str = ''
        try:
            if not record.id:
                text = ERROR_MESSAGE % record._asdict()
            else:
                text = MESSAGE % {
                    **record._asdict(),
                    'location_repl': _repl(record.location),
                    'description_repl':  _repl(record.description),
                }
        except Exception as e:
            logger.error('Ошибка форматирования: %s' % e)

        return text

    @staticmethod
    def format_text(record: Advert | str) -> str:
        text: str = record if isinstance(record, str) else Bot.format_record(record)
        for c in ('.', '_', '-', '+', '(', ')', '!'):  
            text = text.replace(c, '\\' + c) ### экранированить символы
        for c in re.findall(r'\\\\.', text):
            text = text.replace(c, c[-1]) ### разэкрaнировать символы разметки
        return text

    def send_message(self, record: Advert | str, **kwargs) -> None:
        kwargs = {
            'chat_id': self.chat_id,
            'parse_mode': 'MarkdownV2',
            'disable_web_page_preview': True,
            **kwargs,
            'text': Bot.format_text(record),
        }
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(super().send_message(**kwargs))
        except Exception as e:
            logger.error('Ошибка отправки: %s' % e)

    def send_messages(self, texts: list[Advert | str], **kwargs) -> None:
        for x in texts:
            self.send_message(x, **kwargs)
            if len(texts) == 1:
                continue
            sleep(kwargs.get('cooldown', 5))

def send_messages(message: t.Any, **kwargs) -> None:
    if not kwargs:
        logger.warning('Не задана конфигурация отправки: пропустить уведомление')
    else:
        Bot(**kwargs).send_messages(
            message if (
                isinstance(message, t.Iterable) and not isinstance(message, str) 
            ) else [message]
        )
