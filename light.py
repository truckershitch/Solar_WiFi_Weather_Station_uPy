def read_ldr_ads1x15(i2c=None):
    import sys
    from time import sleep
    from machine import I2C, Pin
    import ads1x15
    from user_except import CustomLDRSensorError

    addr = 72 # 0x48
    gain = 1

    rate = 4
    channel = 1

    try:
        if i2c is None:
            sleep(0.5)
            i2c = I2C(scl=Pin(5), sda=Pin(4), freq=400000)
        ads = ads1x15.ADS1115(i2c, addr, gain)

        value = ads.read(rate=rate, channel1=channel)
        # voltage = ads.raw_to_v(value)

        # cleanup
        del ads
        del sys.modules['ads1x15']

        # return (value, voltage)
        return value
    except Exception as e:
        raise CustomLDRSensorError('Error reading LDR sensor: %s' % e) from e

    # ADDR to GND to set address? NOT NEEDED PER ADAFRUIT
