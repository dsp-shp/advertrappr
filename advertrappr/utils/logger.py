from .connector import connect, MODELS
from datetime import datetime
import json
import logging
import typing as t
import sys


FORMAT: str = '%(asctime)s.%(msecs)03d - %(levelname)s - %(module)s.%(funcName)s: %(message)s'

def decorate(cls):
    cls__init__ = cls.__init__
    def __init__(self, name, *args, **kwargs) -> None:
        cls__init__(self, name, *args, **kwargs)
        self.log_to_db: bool = False
        self.name_ = name
        self._handler = logging.StreamHandler(sys.stdout)
        self._handler.setFormatter(logging.Formatter(fmt=FORMAT))
        self.addHandler(self._handler)
    cls.__init__ = __init__

    cls_log = cls._log
    def _log(self, level: int, msg: str, *args, **kwargs) -> None:
        cls_log(self, level, msg, *args, **kwargs)
        fn, lno, func, sinfo = self.findCaller(False, 1)

        if self.log_to_db == True:
            print('log to database')
            return
        
        record = [
            datetime.now(), 
            logging.getLevelName(level), 
            fn.split('/')[-1].split('.')[0] + '.' + func,
            *msg.split(': ', 1)
        ]
        with connect() as con:
            columns = list(MODELS.get('logs').keys())
            schema = ', '.join(columns)
            values = ', '.join(['?'] * len(columns))
            con.execute('insert into logs (%s) values (%s)' % (schema, values), record)
    cls._log = _log

    return cls

def getLogger(name):
    logger = decorate(logging.Logger)(name)
    logging.root.manager.loggerDict['advertrappr__%s' % name] = logger
    return logger

def updateLoggers(**kwargs):
    for l in [logging.getLogger(x) for x in logging.root.manager.loggerDict if (
        x.startswith('advertrappr__')
    )]:
        for k,v in kwargs.items():
            l.__setattr__(k,v)
