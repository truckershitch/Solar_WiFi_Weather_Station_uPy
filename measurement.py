def TakeMeasurement(CONF_WEATHER, calib_factor):
    from machine import Pin, I2C, ADC
    from math import pow, sqrt, fabs
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
    # Reference: https://www.wpc.ncep.noaa.gov/html/heatindex_equation.shtml
    # Calculation is in Fahrenheit
    if temp_C > 26.7:
        c1 = - 42.379
        c2 =    2.04901523
        c3 =   10.14333127
        c4 = -  0.22475541
        c5 = -  6.83783e-3
        c6 = -  5.481717e-2
        c7 =    1.22874e-3
        c8 =    8.5282e-4
        c9 = -  1.99e-6
    
        T = result['temp_F']
        R = result['humidity']
        Tsq = T * T
        Rsq = R * R

        result['heatIndex_F'] = (c1 + c2 * T + c3 * R + c4 * T * R + c5 * Tsq
                                 + c6 * Rsq + c7 * Tsq * R + c8 * T * Rsq + c9 * Tsq * Rsq)

        if T <= 112 and R < 13:
            result['heatIndex_F'] -= ((13 - R) / 4) * sqrt((17 - fabs(T - 95.0)) / 17)
        if T <= 87 and R > 85:
            result['heatIndex_F'] += ((R - 85) / 10) * ((87 - T) / 5)

        output.append('HeatIndex: %.2f °F; ' % result['heatIndex_F'])
    else:
        result['heatIndex_F'] = result['temp_F']
        print('Not warm enough (less than 80.1 °F) for Heat Index')

    # Battery Voltage
    # Voltage Divider R1 = 220k+100k+220k = 540K and R2 = 100k
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
