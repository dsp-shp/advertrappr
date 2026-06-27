from jinja2 import Template
from pathlib import Path
from telegram import Bot as _Bot
from time import sleep
import asyncio
import re
import typing as t

from advertrappr.utils.service import Advert
from advertrappr.utils.logger import getLogger


_TEMPLATES_DIR = Path(__file__).parent / 'templates'
with open(_TEMPLATES_DIR / 'valid.md') as f:
    _VALID = f.read()
with open(_TEMPLATES_DIR / 'invalid.md') as f:
    _INVALID = f.read()

logger = getLogger(__name__)


class Bot(_Bot):
    _temp_valid = Template(_VALID)
    _temp_invalid = Template(_INVALID)

    def format_record(self, record: Advert | str) -> str:
        _repl: t.Callable = lambda x: re.sub(r'\n[\ |\n|\t]*', ' ', x)[:200]

        text: str = ''
        try:
            if not record.id:
                text = self._temp_invalid.render(**record._asdict())
            else:
                text = self._temp_valid.render(**{
                    **record._asdict(),
                    'location_repl': _repl(record.location).replace(' ', '⠀'),
                    'description_repl': _repl(record.description),
                })
        except Exception as e:
            logger.error('Formatting error: %s', e)

        return text

    def format_text(self, record: Advert | str) -> str:
        text: str = record if isinstance(record, str) else self.format_record(record)
        text = text.replace('<br>\n', '\n')
        return text

    def send_message(self, record: Advert | str, **kwargs) -> None:
        kwargs['text'] = self.format_text(record)
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(super().send_message(**kwargs))
        except Exception as e:
            logger.error('Send error: %s', e)

    def send_messages(self, texts: list[Advert | str], cooldown: int = 5, **kwargs) -> None:
        for x in texts:
            self.send_message(x, **kwargs)
            if len(texts) == 1:
                continue
            sleep(cooldown)


def send_messages(message: t.Any, **kwargs) -> None:
    if not ('token' in kwargs and 'chat_id' in kwargs):
        logger.warning('Messenger config not set: skip notification')
    else:
        Bot(kwargs.pop('token')).send_messages(
            message if (
                isinstance(message, t.Iterable) and not isinstance(message, str)
            ) else [message], **kwargs
        )
