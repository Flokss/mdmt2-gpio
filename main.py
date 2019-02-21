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
try:
    from pyA20.gpio import gpio as _gpio
    from pyA20.gpio import port as _port
    _gpio.init()
    GPIO_CFG = _gpio.setcfg
    GPIO_OUTPUT_MODE = _gpio.OUTPUT
    GPIO_OUT = _gpio.output
    LED1 = _port.PA12
    LED2 = _port.PA11
except ImportError:
    import RPi.GPIO as _GPIO
    _GPIO.setmode(_GPIO.BCM)
    _GPIO.setwarnings(False)
    GPIO_CFG = _GPIO.setup
    GPIO_OUTPUT_MODE = _GPIO.OUT
    GPIO_OUT = _GPIO.output
    LED1 = 12
    LED2 = 11


"""
Обязательно. Не пустое имя плагина, тип - str.
Максимальная длинна 30 символов, не должно содержать пробельных символов, запятых и быть строго в нижнем регистре.
Имя плагина является его идентификатором и должно быть уникально.
"""
NAME = 'gpio'


"""
Обязательно. Версия API под которую написан плагин, тип - int.
Если оно меньше config.ConfigHandler.API то плагин не будет загружен, а в лог будет выдано сообщение.
API терминала увеличивается когда публичные методы, их вызов или результат вызова (у cfg, log, owner) изменяется.
API не увеличивается при добавлении новых методов.
Призван защитить терминал от неправильной работы плагинов.
Если API не используется или вам все равно, можно задать заведомо большое число (999999).
"""
API = 30


SETTINGS = 'gpio_config_config'


class Main:
    """
    Обязательно. Точка входа в плагин, должна быть callable.
    Ожидается что это объект класса, экземпляр которого будет создан, но может быть и методом.
    Должен принять 3 аргумента, вызов: Main(cfg=self.cfg, log=self._get_log(name), owner=self.own)
    Может содержать служебные методы и свойства, все они опциональны. Методы должны быть строго callable:
    Методы: start, reload, stop, join.
    Свойства: disable.
    """

    def __init__(self, cfg, log, owner):
        """
        Конструктор плагина.
        :param cfg: ссылка на экземпляр config.ConfigHandler.
        :param log: ссылка на специальный логгер, вызов: log(msg, lvl=logger.Debug)
        :param owner: ссылка на экземпляр loader.Loader
        """
        self.cfg = cfg
        self.log = log
        self.own = owner

        self._events = ('start_record', 'stop_record', 'start_talking', 'stop_talking')
        self._settings = self._get_settings()
        self.disable = False

    @staticmethod
    def _init():
        GPIO_CFG(LED1, GPIO_OUTPUT_MODE)
        GPIO_CFG(LED2, GPIO_OUTPUT_MODE)

    def _led_off(self):
        GPIO_OUT(LED1, not self._settings['led_on'])
        GPIO_OUT(LED2, not self._settings['led_on'])

    def start(self):
        self._init()
        self._led_off()
        self.own.subscribe(self._events, self._callback)

    def stop(self):
        self.own.unsubscribe(self._events, self._callback)
        self._led_off()

    def _callback(self, name, *_, **__):
        led_on = self._settings['led_on']
        if name == 'start_talking':
            GPIO_OUT(LED1, led_on)
            self.log('start_talking LED1 on')
        elif name == 'stop_talking':
            GPIO_OUT(LED1, not led_on)
            self.log('stop_talking LED1 off')
        elif name == 'start_record':
            GPIO_OUT(LED2, led_on)
            self.log('start_record LED2 on')
        elif name == 'stop_record':
            GPIO_OUT(LED2, not led_on)
            self.log('stop_record LED2 off')

    def _get_settings(self) -> dict:
        def_cfg = {'led_on': 1}
        cfg = self.cfg.load_dict(SETTINGS)
        if isinstance(cfg, dict):
            is_ok = True
            for key, val in def_cfg.items():
                if key not in cfg or not isinstance(cfg[key], type(val)):
                    is_ok = False
                    break
            if is_ok:
                return cfg
        self.cfg.save_dict(SETTINGS, def_cfg, True)
        return def_cfg
