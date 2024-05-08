from .connector import MODELS
from collections import namedtuple
from typing_extensions import Self
import abc
import typing as t


Advert: type = namedtuple(
    'Advert', MODELS.get('advs').keys(), defaults=(None,) * len(MODELS.get('advs')) 
)

class Service(abc.ABC):
    def __new__(cls, **kwargs) -> Self:
        from . import parsers
        
        service = kwargs.get('service') 
        if not service:
            return super().__new__(cls, **kwargs)
        if not vars(parsers).get(service):
            raise Exception('Не обнаружен сервисный модуль для %s' % service)
        
        service_object = object.__new__(vars(parsers).get(service))
        kwargs.pop('service')
        service_object.__init__(**kwargs)
        return service_object

    @staticmethod
    @abc.abstractmethod
    def parse(*args, **kwargs) -> list[Advert]:
        """ Парсинг записей из исходного кода """

def getService(service: str, **kwargs) -> Service:
    return Service.__new__(Service, service=service, **kwargs)
