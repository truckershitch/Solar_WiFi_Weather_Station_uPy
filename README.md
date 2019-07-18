# Solar_WiFi_Weather_Station_uPy
Based on the work of Open Green Energy and 3KUdelta.  Written in MicroPython

This project is based on 3KUDelta's fork of the work done by the Open Energy Project.  It is in Micropython.

This works best if the modules are compiled and frozen into the firmware.  It will probably work without doing this but most of my testing has been done with frozen modules.

Requires [blynklib][1] and [bme280_float][2] libraries.  Also requires [umqtt.simple][3]

[1]: https://github.com/blynkkk/lib-python
[2]: https://github.com/robert-hh/BME280/blob/master/bme280_float.py
[3]: https://github.com/micropython/micropython-lib/tree/master/umqtt.simple
