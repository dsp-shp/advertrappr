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
            datetime.now(),
            logging.getLevelName(level),
            fn.split('/')[-1].split('.')[0] + '.' + func,
            *[*msg.split(': ', 1), None][:2],
        )
        with connect() as con:
            columns = list(MODELS.get('logs').keys())
            schema = ', '.join(columns)
            values = ', '.join(['?'] * len(columns))
            con.execute(
                'insert into logs (%s) values (%s)' % (schema, values), 
                record.values()
            )
    return wrapper

def getLogger(name):
    logger = logging.getLogger(name)
    logging.basicConfig(**CONFIG)
    logger.__setattr__('log_to_db', False)
    logger._log = decorate(logger, logger._log)
    return logger

def updateLoggers(**kwargs):
    for l in [logging.getLogger(x) for x in logging.root.manager.loggerDict 
    # if (x.startswith('advertrappr__'))
    ]:
        for k,v in kwargs.items():
            l.__setattr__(k,v)

def getCommonHandler():
    _h = None
    loggers = [logging.getLogger(x) for x in logging.root.manager.loggerDict if (
        x.startswith('advertrappr__')
    )]
    print(loggers)
    for l in loggers:
        if l.handlers and not _h:
            _h = l.handlers[0]
    if not _h:
        _h = logging.StreamHandler(sys.stdout)
        _h.setFormatter(logging.Formatter(fmt=FORMAT))
    return _h 

