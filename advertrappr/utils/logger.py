from datetime import datetime
import logging
import typing as t
import sys


CONFIG: dict[str, t.Any] = {
    'level': logging.INFO,
    'datefmt': '%Y-%m-%d %H:%M:%S',
    'format': '%(asctime)s.%(msecs)03d - %(levelname)s - %(module)s.%(funcName)s: %(message)s'
}

def decorate(self, f):
    def wrapper(level: int, msg: str, *args, **kwargs): 
        f(level, msg, *args, **kwargs)

        if not self.log_to_db:
            return

        from .connector import connect, MODELS

        fn, lno, func, sinfo = self.findCaller(False, 1)
        record: tuple = (
            logging.getLevelName(level),
            fn.split('/')[-1].split('.')[0] + '.' + func,
            *[*(msg.split(': ', 1) if not isinstance(msg, Exception) else (str(msg), None)), None][:2],
            datetime.now(),
        )
        with connect() as con:
            con.table('logs').insert(record)
            
    return wrapper

def getLogger(name):
    logger = logging.getLogger(name)
    logging.basicConfig(**CONFIG)
    logger.__setattr__('log_to_db', False)
    logger._log = decorate(logger, logger._log)
    return logger

def updateLoggers(**kwargs):
    """ Обновление логгеров

    Функция обновляет все логгеры, указанные в loggerDict словаре корневого менеджера.
    Так, например, функцией задается процесс логирования в базу данных: 
        updateLogger(log_to_db = True)

    """
    for l in [logging.getLogger(x) for x in logging.root.manager.loggerDict]:
        for k,v in kwargs.items():
            l.__setattr__(k,v)
