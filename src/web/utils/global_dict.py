class GlobalDict(dict):
    """Класс глобального словаря, необходимый для общего доступа к данным из разных модулей"""

    def __new__(cls, name):
        if not hasattr(cls, 'instance'):
            cls.instance = super(GlobalDict, cls).__new__(cls)
        if name not in cls.instance:
            cls.instance[name] = {}
        return cls.instance[name]
