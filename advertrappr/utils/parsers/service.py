import abc

class Service(abc.ABC):
    @staticmethod
    @abc.abstractmethod
    def parse(*args, **kwargs) -> list[dict]:
        """ Метод парсинга структурированной информации из исходного кода

        Возвращает:
            list[dict]: список словарей

        """
        pass
