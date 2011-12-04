
class MetaSingleton(type):

    def __init__(cls, name, bases, dic):
        super(MetaSingleton, cls).__init__(name, bases, dic)
        cls.__instance = None

    def __call__(cls, *args, **kwargs):
        if cls.__instance is None:
            cls.__instance = super(MetaSingleton, cls).__call__(*args, **kwargs)
        return cls.__instance


class Singleton(object):

    __metaclass__ = MetaSingleton

    @classmethod
    def getInstance(cls):
        return cls._MetaSingleton__instance

