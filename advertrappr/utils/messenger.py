from .logger import getLogger
from telegram import Bot as _Bot
from collections import namedtuple
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
    def escape_format(text: str) -> str:
        for c in ('.', '_', '-', '+', '(', ')', '!'):  
            text = text.replace(c, '\\' + c) ### экранированить символы
        for c in re.findall(r'\\\\.', text):
            text = text.replace(c, c[-1]) ### разэкрaнировать символы разметки
        return text

    @staticmethod
    def format_message(n: namedtuple) -> str:
        _repl: t.Callable = lambda x: re.sub(
            r'\n[\ |\n|\t]*', ' ', x ### заменить все отступы символом пробела, 
        ).replace(' ', '⠀')[:200] ### заменить все пробелы на неразрывные и обрезать
        
        text: str
        if not n.id:
            text = ERROR_MESSAGE % n._asdict()
        else:
            text = MESSAGE % {
                **n._asdict(),
                'location_repl': _repl(n.location),
                'description_repl':  _repl(n.description),
            }

        return t.Self.escape_format(text)

    def send_message(self, text: str,  **kwargs) -> None:
        kwargs = {
            'chat_id': self.chat_id,
            'parse_mode': 'MarkdownV2',
            'disable_web_page_preview': True,
            **kwargs,
            'text': t.Self.format_message(text),
        }
        try:
            asyncio.run(super().send_message(**kwargs))
        except Exception as e:
            pass # TODO: залогировать ошибку

    def send_messages(self, texts: list[str], cooldown: int = 5, **kwargs) -> None:
        for x in texts:
            send_message(x, **kwargs)
            wait(cooldown)
