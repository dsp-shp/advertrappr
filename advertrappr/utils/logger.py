from datetime import datetime
import logging
import sys
import typing as t

from advertrappr.utils.connector import connect


LOG_CONFIG: dict[str, t.Any] = {
    'level': logging.INFO,
    'datefmt': '%Y-%m-%d %H:%M:%S',
    'format': '%(asctime)s.%(msecs)03d - %(levelname)s - %(module)s.%(funcName)s: %(message)s',
}


class DBHandler(logging.Handler):
    def __init__(self, level: int = logging.NOTSET) -> None:
        super().__init__(level)

    def emit(self, record: logging.LogRecord) -> None:
        try:
            with connect() as con:
                con.table('logs').insert((
                    record.levelname,
                    f'{record.module}.{record.funcName}',
                    record.getMessage(),
                    str(record.args) if record.args else '',
                    datetime.now(),
                ))
        except Exception:
            self.handleError(record)


def getLogger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(LOG_CONFIG['level'])
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(
            fmt=LOG_CONFIG['format'],
            datefmt=LOG_CONFIG['datefmt'],
        ))
        logger.addHandler(handler)
    return logger


def addDBHandler(logger: logging.Logger | None = None) -> None:
    targets = [logger] if logger else [
        logging.getLogger(n) for n in logging.root.manager.loggerDict
    ]
    for l in targets:
        if not any(isinstance(h, DBHandler) for h in l.handlers):
            l.addHandler(DBHandler())
