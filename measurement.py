def TakeMeasurement(CONF_WEATHER):
    from machine import Pin, I2C, ADC
    from math import pow
    from time import sleep
    import sys
    import bme280_float # https://github.com/robert-hh/BME280

    result = {}

    def convertToF(tempC):
        return tempC * 1.8 + 32

    i2c = I2C(scl=Pin(5), sda=Pin(4))
    bme = bme280_float.BME280(i2c=i2c)

    # wait a sec
    sleep(1)

    # read data from bme280
    bme_data_tph = bme.read_compensated_data()

    # Get Temperature
    # result['temp_C'] = bme_data_tph[0] + CONF_WEATHER['TEMP_CORR']
    # result['temp_F'] = convertToF(result['temp_C'])
    temp_C = bme_data_tph[0] + CONF_WEATHER['TEMP_CORR']
    result['temp_F'] = convertToF(temp_C)

    # output = ['Temp: %.2f °C, %.2f °F; ' % (result['temp_C'], result['temp_F'])]
    output = ['Temp: %.2f °C, %.2f °F; ' % (temp_C, result['temp_F'])]

    # Get Humidity
    result['humidity'] = bme_data_tph[2]
    output.append('Humidity: %.2f %%; ' % result['humidity'])

    # Get Pressure
    # result['measured_Pres_hPa'] = bme_data_tph[1] / 100
    measured_Pres_hPa = bme_data_tph[1] / 100
    result['measured_Pres_inHg'] = bme_data_tph[1] / 3386.38867
    # output.append('Pressure: %.2f hPa, %.2f inHg; ' % (result['measured_Pres_hPa'], result['measured_Pres_inHg']))
    output.append('Pressure: %.2f hPa, %.2f inHg; ' % (measured_Pres_hPa, result['measured_Pres_inHg']))

    # Calculate Relative Pressure
    # SLPressure_hPa = (((measured_Pres_hPa * 100.0)/pow((1-(float(CONF_WEATHER['ELEVATION']))/44330), 5.255))/100.0)
    # https://keisan.casio.com/exec/system/1224575267
    SLPressure_hPa = measured_Pres_hPa * pow(1 - .0065 * CONF_WEATHER['ELEVATION']
                                             / (temp_C + 273.15 + .0065 * CONF_WEATHER['ELEVATION']), -5.257)
    result['rel_Pres_Rounded_hPa'] = round(SLPressure_hPa)
    result['rel_Pres_inHg'] = (SLPressure_hPa) / 33.8638867
    output.append('Pressure rel: %d hPa, %.2f inHg; ' % (result['rel_Pres_Rounded_hPa'], result['rel_Pres_inHg']))

    # Get Dewpoint
    # result['dewPt_C'] = bme.dew_point
    # result['dewPt_F'] = convertToF(result['dewPt_C'])
    result['dewPt_F'] = convertToF(bme.dew_point)
    # output.append('Dewpoint: %.2f °C, %.2f °F; ' % (result['dewPt_C'], result['dewPt_F']))
    output.append('Dewpoint: %.2f °F; ' % result['dewPt_F'])

    # Dewpoint Spread
    result['dewPtSpread_F'] = result['temp_F'] - result['dewPt_F']
    output.append('Dewpoint Spread: %.2f °F; ' % result['dewPtSpread_F'])

    # Calculate HI (heatindex) --> HI starts working above 26.7°C
    if temp_C > 26.7:
        c1 = -8.784
        c2 = 1.611
        c3 = 2.338
        c4 = -0.146
        c5 = -1.230e-2
        c6 = -1.642e-2
        c7 = 2.211e-3
        c8 = 7.254e-4
        c9 = -2.582e-6
        
        T = temp_C
        R = result['humidity']
    
        A = ((c5 * T) + c2) * T + c1
        B = ((c7 * T) + c4) * T + c3
        C = ((c9 * T) + c8) * T + c6
        # result['heatIndex_C'] = (C * R + B) * R + A
        # result['heatIndex_F'] = convertToF(result['heatIndex_C'])
        result['heatIndex_F'] = convertToF((C * R + B) * R + A)
        # output.append('HeatIndex: %.2f °C, %.2f °F; ' % (result['heatIndex_C'], result['heatIndex_F']))
        output.append('HeatIndex: %.2f °F; ' % result['heatIndex_F'])
    else:
        # result['heatIndex_C'] = result['temp_C']
        result['heatIndex_F'] = result['temp_F']
        # print('Not warm enough (less than 26.7 °C) for Heat Index')
        print('Not warm enough (less than 80.1 °F) for Heat Index')

    # Battery Voltage
    # Voltage Divider R1 = 220k+100k+220k = 540K and R2 = 100k
    calib_factor = 5.1315 # varies -- fix for your battery
    adc = ADC(0)
    raw = adc.read()
    result['volt'] = raw * calib_factor / 1024
    output.append('Voltage: %.2f V\n' % result['volt'])

    #print(''.join(output))
    for item in output:
        print('%s' % item, end='')
    del output
    # round floats to 2 decimal places
    result = dict(zip(result, map(lambda x: round(x, 2) if isinstance(x, float) else x, result.values())))

    del bme
    del sys.modules['bme280_float']

    return result
