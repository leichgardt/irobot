import os
import requests
import re
from pathlib import Path


__all__ = 'config',


class Configer:

    """
    Класс для загрузки конфигураций из файла.
    Пример содержания файла config.txt:

    ###################
    [TelegramBot]
    # token to bot access
    User=tele_user
    Token=xxxyyyzzz

    [Lanbilling]
    Host=192.168.1.10
    User=admin
    Password=123

    ###################

    Вызов объекта класса выдаст загруженные данные или, если данных не было, выдаст установленное value
    >>> cfg = Configer(url='/path/to/config.txt').load(url='/path/to/config.txt')
    >>> print('1 user =', cfg('telegrambot', 'user', 'MyUsername'))
    >>> print('2 url  =', cfg('lanbilling', 'url', 'http://some.url/'))

    Вывод:
    1 user = admin
    2 url  = http://some.url/

    """

    def __init__(self, **kwargs):
        self.url = kwargs.get('url', 'localhost')
        self.config_list = {}
        self.user = ''
        self.__passwd = ''

    def _check(self):
        if not self.config_list:
            self.load()

    def __getitem__(self, module: str):
        self._check()
        module = module.lower().replace('\n', '').replace('[', '').replace(']', '').strip()
        if module not in self.config_list.keys():
            self.config_list.update({module: {}})
        return self.config_list[module]

    def __call__(self, module, param, value=None):
        self._check()
        module = module.lower().replace('\n', '').replace('[', '').replace(']', '').strip()
        if module not in self.config_list.keys():
            self.config_list.update({module: {}})
        if param not in self.config_list[module].keys():
            self.config_list[module].update({param: value})
        return self.config_list[module][param]

    def config_params(self, filepath='config_params.txt'):
        if not os.path.exists(filepath):
            raise FileNotFoundError(filepath)
        with open(filepath, 'r') as f:
            text = [line.replace('\n', '').strip() for line in f.readlines()]
            self.url = text[0]
            self.user = text[1]
            self.__passwd = text[2]

    def load(self):
        if not self.user or not self.__passwd:
            self.config_params()
        print('Uploading configuration from {}'.format(self.url))
        self.config_list = {}
        try:
            resp = requests.get(self.url, auth=(self.user, self.__passwd), timeout=5)
        except requests.Timeout:
            print(f'Server doesn\'t respond: {self.url}')
            exit(1)
        else:
            resp.encoding = resp.apparent_encoding
            text = re.split("([^\n]*\n)", resp.text)[1::2]
            current_module = ''
            for line in text:
                if line[0] == '#':
                    continue
                elif line[0] == '[' and ']' in line:
                    module = line[1:].replace('\n', '').replace(']', '').strip().lower()
                    current_module = module
                    self.config_list.update({module: {}})
                elif current_module and line and line != '\n':
                    key, value = line.replace('\n', '').split('=', 1)
                    self.config_list[current_module].update({key.lower().strip(): value})
        return self


config = Configer()
path = Path(__file__).parent / 'config_params.txt'
config.config_params(str(path.resolve()))
