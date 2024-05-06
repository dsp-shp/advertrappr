from typing_extensions import Self
import abc
import typing as t


class Service():
    def __new__(cls, **kwargs) -> Self:
        service, parsers = kwargs.pop('service'), kwargs.pop('parsers')
        if not vars(parsers).get(service):
            raise Exception('Передан некорректный "service": %s' % service)
        
        service_object = object.__new__(vars(parsers).get(service))
        service_object.__init__(**kwargs)
        return service_object

    @staticmethod
    ### @abc.abstractmethod
    def parse(*args, **kwargs) -> list[dict]:
        """ Метод парсинга структурированной информации из исходного кода

        Возвращает:
            list[dict]: список словарей

        """
        pass

def __init__(service: str, **kwargs) -> Service:
    from . import parsers

    return Service.__new__(Service, **{**kwargs, 'service': service, 'parsers': parsers})
