"""
Технически, плагины являются модулями и мало чем отличаются от базовых систем загружаемых в loader.py,
но т.к. "модули" уже заняты - пусть будут плагины. Основные отличия плагинов:
- Хранятся в директории src/plugins/, содержимое которой занесено в .gitignore терминала.
- Загружаются и запускаются динамически после запуска всех базовых систем терминала. Первыми завершают свою работу.
- Терминал никак не зависит от плагинов.

Путь до плагина выглядит как mdmTerminal2/src/plugins/folder/main.py, где:
folder - директория с плагином, ее имя не имеет значения.
main.py - динамически загружаемый файл модуля. Терминал игнорирует остальные файлы и никак их не использует.

Для успешной инициализации плагина, main.py должен содержать определенные свойства и точку входа (Main).
"""

import threading
import os
import sys
import requests
from time import sleep
from pyA20.gpio import gpio
from pyA20.gpio import port
import logger
from languages import LANG_CODE
from modules_manager import DynamicModule, Say, NM, EQ
from utils import REQUEST_ERRORS

"""
Обязательно. Не пустое имя плагина, тип - str.
Максимальная длинна 30 символов, не должно содержать пробельных символов, запятых и быть строго в нижнем регистре.
Имя плагина является его идентификатором и должно быть уникально.
"""
NAME = 'gpio'
led = port.PA12
led1 = port.PA11
led2 = port.PA6
gpio.init()
gpio.setcfg(led, gpio.OUTPUT)
gpio.setcfg(led1, gpio.OUTPUT)
gpio.setcfg(led2, gpio.OUTPUT)
gpio.output(led, 1)
gpio.output(led1, 1)
"""
Обязательно. Версия API под которую написан плагин, тип - int.
Если оно меньше config.ConfigHandler.API то плагин не будет загружен, а в лог будет выдано сообщение.
API терминала увеличивается когда публичные методы, их вызов или результат вызова (у cfg, log, owner) изменяется.
API не увеличивается при добавлении новых методов.
Призван защитить терминал от неправильной работы плагинов.
Если API не используется или вам все равно, можно задать заведомо большое число (999999).
"""
API = 665

"""
Опционально. None или итерируемый объект.
Содержит секции из конфига, удаленное изменение которых вызовет метод reload() у точки входа (при наличии).
Если вызов reload завершится ошибкой, то больше он вызываться не будет (пока терминал не перезапустится).
Если объект dict и значение секции итерируемое, то будут сравниваться ключи в секции.
Примеры:
# Вызов при изменении [settings] lang или [modules] allow
{'settings': ('lang',), 'modules': {'allow': ''}}
# Вызов при изменении секции mpd, models или log
('mpd', 'models' 'log')
"""
CFG_RELOAD = {'settings': ('lang',)}

"""
Опционально.
Если bool(DISABLE) == True, терминал прекратит проверку модуля и не загрузит плагин.
Проверяется первым.
"""
# DISABLE = False


class Main(threading.Thread):
    """
    Обязательно. Точка входа в плагин, должна быть callable.
    Ожидается что это объект класса, экземпляр которого будет создан, но может быть и методом.
    Должен принять 3 аргумента, вызов: Main(cfg=self.cfg, log=self._get_log(name), owner=self.own)
    Может содержать служебные методы и свойства, все они опциональны. Методы должны быть строго callable:
    Методы: start, reload, stop, join.
    Свойства: disable.
    """
    INTERVAL = 3600 * 12

    def __init__(self, cfg, log, owner):
        """
        Конструктор плагина.
        :param cfg: ссылка на экземпляр config.ConfigHandler.
        :param log: ссылка на специальный логгер, вызов: log(msg, lvl=logger.Debug)
        :param owner: ссылка на экземпляр loader.Loader
        """
        super().__init__()
        self.cfg = cfg
        self.log = log
        self.own = owner

        self._wait = threading.Event()
        self._work = False
        self._events = (
            'speech_recognized_success', 'voice_activated', 'ask_again',
            'music_status', 'start_record', 'stop_record', 'start_talking', 'stop_talking',
            'volume', 'music_volume',
            'updater',
        )

        self.disable = False

    def start(self):
        """
        Опционально. Вызывается после того как все плагины будут созданы.
        Вызов метода также будет отражен в логе.
        При любой ошибке терминал сочтет плагин сломанным и будет его игнорировать.
        :return: None
        """
        self.reload()
        self._work = True
        super().start()

    def join(self, timeout=None):
        """
        Опционально. Вызывается при завершении терминала. Будет вызван и при отсутствии start().
        В лог будут добавлены сообщения до и после вызова.
        :return: None
        """
        self._unsubscribe()
        self._work = False
        self._wait.set()
        super().join(timeout)

    def reload(self):
        """
        Опционально. Вызывается при изменении конфигурации согласно CFG_RELOAD.
        Вызов этого метода будет отражен в логе.
        При любой ошибке терминал сочтет reload() сломанным и больше не будет его вызывать.
        :return: None
        """
        self.disable = LANG_CODE.get('ISO') != 'ru'
        if self.disable:
            self._unsubscribe()
        else:
            self._subscribe()

    def stop(self):
        """
        Опционально. Вызывается при завершении терминала, если join() отсутствует.
        Вызов этого метода будет отражен в логе.
        :return: None
        """
        raise RuntimeError('Never!')

    def run(self):
        while self._work:
            self._wait.wait(self.INTERVAL)
            if self._wait.is_set():
                self._wait.clear()
                continue
            if self.disable:
                continue
            try:
                msg = random_quotes()
            except RuntimeError as e:
                self.log(e, logger.WARN)
            else:
                self.own.say(msg)

    def _callback(self, name, data=None, *_, **__):
        #self._wait.set()
        if name=='start_talking':
            gpio.output(led, 0)
            self.log('LED1 on', logger.DEBUG)

        if name == 'stop_talking':
            gpio.output(led, 1)
            self.log('LED1 off', logger.DEBUG)

        if name == 'start_record':
            gpio.output(led1, 0)
            self.log('LED2 on', logger.DEBUG)

        if name == 'stop_record':
            gpio.output(led1, 1)
            self.log('LED2 off', logger.DEBUG)

        self.log(name, logger.DEBUG)

    def _mod_callback(self, *_):
        try:
            return Say(random_quotes())
        except RuntimeError as e:
            self.log(e, logger.DEBUG)

    def _subscribe(self):
        self.own.subscribe(self._events, self._callback)
        #self.own.insert_module(DynamicModule(self._mod_callback, NM, [['скажи афоризм', EQ], ['расскажи афоризм', EQ]]))

    def _unsubscribe(self):
        self.own.unsubscribe(self._events, self._callback)
        self.own.extract_module(self._mod_callback)


def random_quotes() -> str:
    params = {
        'method': 'getQuote',
        'format': 'json',
        'lang': 'ru',
        'key': '',
    }
    try:
        result = requests.post('http://api.forismatic.com/api/1.0/', params=params)
    except REQUEST_ERRORS as e:
        raise RuntimeError('Request error: {}'.format(e))
    if not result.ok:
        raise RuntimeError('Server error {}:{}'.format(result.status_code, result.reason))
    try:
        msg = result.json()['quoteText'][:200]
    except (TypeError, KeyError, ValueError) as e:
        raise RuntimeError('Parsing error: {}, {}'.format(e, result.text[:200]))
    if not msg:
        raise RuntimeError('Empty quote')
    return msg
