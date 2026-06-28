from jinja2 import Template
from pathlib import Path
from telegram import Bot as _Bot, InputMediaPhoto
from telegram.constants import ParseMode
from time import sleep
import asyncio
import json
import re
import typing as t
import io
import requests

from advertrappr.settings import Settings
from advertrappr.utils.services.service import Advert, getLogger


logger = getLogger(__name__)


class Bot(_Bot):
    _temp_valid = Template((Settings.temp_path / 'valid.md').read_text())
    _temp_invalid = Template((Settings.temp_path / 'invalid.md').read_text())

    def format_record(self, record: Advert | str) -> str:
        _repl: t.Callable = lambda x: re.sub(r'\n[\ |\n|\t]*', ' ', x)[:200]

        text: str = ''
        try:
            if not record.id:
                text = self._temp_invalid.render(**record._asdict())
            else:
                text = self._temp_valid.render(**{
                    **record._asdict(),
                    'location': re.sub(r'[\ ]+', ' ', record.location),
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

    def send_messages(self, texts: list[Advert | str], cooldown: int = 5, **kwargs) -> None:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                for i, x in enumerate(texts):
                    if len(images := [*json.loads(x.images)]) < 5:
                        images = [*images, *(['']*5)][:5]

                    kwargs['media'] = [InputMediaPhoto(
                        media=download_photo_to_memory(y),
                        **({} if j != 0 else {"caption": self.format_text(x), "parse_mode": ParseMode.HTML})
                    ) for j, y in enumerate(images)]
                    loop.run_until_complete(super().send_media_group(**kwargs))
                    if i != len(texts) - 1:
                        loop.run_until_complete(asyncio.sleep(cooldown))
            finally:
                loop.close()


headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}
placeholder = io.BytesIO(requests.get(
    'https://upload.wikimedia.org/wikipedia/commons/5/59/Empty.png', headers=headers, timeout=10
).content)
placeholder.name = "placeholder.png"


def download_photo_to_memory(url: str) -> io.BytesIO:
    if not url:
        placeholder.seek(0)
        return placeholder
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            file_like = io.BytesIO(response.content)
            file_like.name = "photo.jpg"
            return file_like
            
        raise Exception(f"Failed to download image. Status-code: {response.status_code} for: \"{url}\"")
    except Exception as e:
        logger.error(f"Failed to download image at \"{url}\": {e}")
        placeholder.seek(0)
        return placeholder



def send_messages(message: t.Any, **kwargs) -> None:
    if not ('token' in kwargs and 'chat_id' in kwargs):
        logger.warning('Messenger config not set: skip notification')
    else:
        Bot(kwargs.pop('token')).send_messages(
            message if (
                isinstance(message, t.Iterable) and not isinstance(message, str)
            ) else [message], **kwargs
        )
