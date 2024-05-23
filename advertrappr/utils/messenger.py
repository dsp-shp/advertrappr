from . import Advert, getLogger, templates
from jinja2 import Template
from telegram import Bot as _Bot
from time import sleep
import asyncio
import os
import re
import typing as t


with open(os.path.join(templates.__path__._path[0], 'valid.md'), 'r') as valid, \
     open(os.path.join(templates.__path__._path[0], 'invalid.md'), 'r') as invalid:
    TEMPLATES = {'valid': valid.read(), 'invalid': invalid.read(),}

logger = getLogger(__name__)

class Bot(_Bot):
    _temp_valid: Template
    _temp_invalid: Template

    def __init__(self, token: str, temps: dict = {}) -> None:
        super().__init__(token)
        self._temp_valid = temps.get('valid') or Template(TEMPLATES['valid']) 
        self._temp_invalid = temps.get('invalid') or Template(TEMPLATES['invalid'])

    def format_record(self, record: Advert | str) -> str:
        ### заменить все отступы символом пробела
        _repl: t.Callable = lambda x: re.sub(r'\n[\ |\n|\t]*', ' ', x)[:200]
        
        text: str = ''
        try:
            if not record.id:
                text = self._temp_invalid.render(**record._asdict())
            else:
                text = self._temp_valid.render(**{
                    **record._asdict(),
                    'location_repl': _repl(record.location).replace(' ', '⠀'),
                    'description_repl':  _repl(record.description),
                })
        except Exception as e:
            logger.error('Ошибка форматирования: %s' % e)

        return text

    def format_text(self, record: Advert|str) -> str:
        text: str = record if isinstance(record, str) else self.format_record(record)
        text = text.replace('<br>\n', '\n')
        #for c in ('.', '_', '-', '+', '(', ')', '!'):
        #    text = text.replace(c, '\\' + c) ### экранированить символы
        #for c in re.findall(r'\\\\.', text):
        #    text = text.replace(c, c[-1]) ### разэкрaнировать символы разметки
        return text

    def send_message(self, record: Advert|str, **kwargs) -> None:
        kwargs['text'] = self.format_text(record)
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(super().send_message(**kwargs))
        except Exception as e:
            logger.error('Ошибка отправки: %s' % e)

    def send_messages(self, texts: list[Advert|str], cooldown: int = 5, **kwargs) -> None:
        for x in texts:
            self.send_message(x, **kwargs)
            if len(texts) == 1:
                continue
            sleep(cooldown)

def send_messages(message: t.Any, **kwargs) -> None:
    if not ('token' in kwargs and 'chat_id' in kwargs):
        logger.warning('Не задана конфигурация отправки: пропустить уведомление')
    else:
        templates = kwargs.pop('templates') if kwargs.get('templates') else {}
        Bot(kwargs.pop('token'), templates).send_messages(
            message if (
                isinstance(message, t.Iterable) and not isinstance(message, str) 
            ) else [message], **kwargs
        )
