# Опытный образец плагина для  [mdmTerminal2](https://github.com/Aculeasis/mdmTerminal2)

для работы плагина необходимо чтобы  [mdmTerminal2](https://github.com/Aculeasis/mdmTerminal2) запускался с root правами
# Установка
```


# для плат на процессорах H2+ и H3
cd ~
git clone https://github.com/duxingkei33/orangepi_PC_gpio_pyH3
cd orangepi_PC_gpio_pyH3
~/mdmTerminal2/env/bin/python -m setup.py install
cd ~/mdmTerminal2/src/plugins
git clone https://github.com/Flokss/mdmt2-gpio


# для плат на процессорах H5
cd ~
git clone https://github.com/herzig/orangepi_PC_gpio_pyH5
cd orangepi_PC_gpio_pyH5
~/mdmTerminal2/env/bin/python -m setup.py install
cd ~/mdmTerminal2/src/plugins
git clone https://github.com/Flokss/mdmt2-gpio


# для Raspberry Pi3 
cd ~
~/mdmTerminal2/env/bin/python -m pip install RPi.GPIO
cd ~/mdmTerminal2/src/plugins
git clone https://github.com/Flokss/mdmt2-gpio
```
И перезапустить терминал.
# Описание
Плагин управляет светодиодами подключенными к плате
```
 LED1  при проговаривании текста терминалом
 LED2  при записи голоса
```
# Настройка
Настройки хранятся в mdmTerminal2/src/data/gpio_config_config.json, файл будет создан при первом запуске:
```
Для плат Orange Pi настройки при первом запуске LED1=12, LED2=11 (только GPIO PA)
Для плат Raspberry Pi настройки при первом запуске LED1=20, LED2=21 (нумерация BCM)
```
```
led_on: логический уровень включенного светодиода 0 или 1, по умолчанию 1
LED1: пин GPIO светодиода для событий start_talking и stop_talking 
LED2: пин GPIO светодиода для событий start_record и stop_record
```
