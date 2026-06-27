from datetime import datetime
from dataclasses import dataclass, fields

import logging
import sys
import typing as t


LOG_FORMAT = '%(asctime)s.%(msecs)03d - %(levelname)s - %(module)s.%(funcName)s: %(message)s'
LOG_DATEFMT = '%Y-%m-%d %H:%M:%S'


@dataclass
class Log:
    level: str
    func: str
    text: str
    args: str


class DBHandler(logging.Handler):
    def __init__(self, level: int = logging.NOTSET) -> None:
        super().__init__(level)

    def emit(self, record: logging.LogRecord) -> None:
        from advertrappr.settings import settings

        try:
            settings.db_conn.execute(
                'INSERT INTO logs (%s) VALUES (%s)' % (
                    ', '.join(f.name for f in fields(Log)),
                    ', '.join(['?'] * len(fields(Log))),
                ),
                [
                    record.levelname,
                    f'{record.module}.{record.funcName}',
                    record.getMessage(),
                    str(record.args) if record.args else '',
                ],
            )
        except Exception:
            self.handleError(record)


def getLogger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(fmt=LOG_FORMAT, datefmt=LOG_DATEFMT))
        logger.addHandler(handler)
    return logger


def addDBHandler() -> None:
    for l in [logging.getLogger(n) for n in logging.root.manager.loggerDict]:
        if not any(isinstance(h, DBHandler) for h in l.handlers):
            l.addHandler(DBHandler())
