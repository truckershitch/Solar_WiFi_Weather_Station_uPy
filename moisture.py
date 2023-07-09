import sys
from machine import I2C, Pin
from time import sleep
import ads1x15
from user_except import CustomHWError

addr = 72 # 0x48
gain = 1

rate = 4
channel = 0

def take_moisture(i2c=None):
    try:
        if i2c is None:
            sleep(0.5)
            i2c = I2C(scl=Pin(5), sda=Pin(4), freq=400000)
        ads = ads1x15.ADS1115(i2c, addr, gain)

        value = ads.read(rate=rate, channel1=channel)
    except Exception as e:
        raise CustomHWError('Error reading moisture sensor: %s' % e)
    
    voltage = ads.raw_to_v(value)

    # cleanup
    del ads
    del sys.modules['ads1x15']

    return (value, voltage)

# ADDR to GND to set address? NOT NEEDED PER ADAFRUIT