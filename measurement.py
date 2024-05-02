from machine import ADC
from math import pow, sqrt, fabs
from time import sleep
import sys
import bme280_int

def TakeMeasurement(CONF_WEATHER, calib_factor, i2c):
    result = {}

    def convertToF(tempC):
        return tempC * 1.8 + 32

    bme = bme280_int.BME280(i2c=i2c)

    # wait a sec
    sleep(0.5)

    # read data from bme280
    bme_data_tph = bme.read_compensated_data()

    # Get Temperature
    temp_C = bme_data_tph[0] / 100.0 + CONF_WEATHER['TEMP_CORR']
    result['temp_F'] = convertToF(temp_C)

    output = ['Temp: %.2f °C, %.2f °F; ' % (temp_C, result['temp_F'])]

    # Get Humidity
    result['humidity'] = bme_data_tph[2] / 1024.0
    output.append('Humidity: %.2f %%; ' % result['humidity'])

    # Get Pressure
    measured_Pres_hPa = bme_data_tph[1] / 25600.0
    #result['measured_Pres_inHg'] = bme_data_tph[1] / 3386.38867
    result['measured_Pres_inHg'] = bme_data_tph[1] / 866915.49952
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
    result['dewPt_F'] = convertToF(bme.dew_point / 100 + CONF_WEATHER['TEMP_CORR'])
    # output.append('Dewpoint: %.2f °C, %.2f °F; ' % (result['dewPt_C'], result['dewPt_F']))
    output.append('Dewpoint: %.2f °F; ' % result['dewPt_F'])

    # Dewpoint Spread
    result['dewPtSpread_F'] = result['temp_F'] - result['dewPt_F']
    output.append('Dewpoint Spread: %.2f °F; ' % result['dewPtSpread_F'])

    def heat_index():
        # Calculate HI (heatindex) --> HI starts working above 26.7°C
        # Reference: https://www.wpc.ncep.noaa.gov/html/heatindex_equation.shtml
        # See also: https://brownmath.com/bsci/notheat.htm#Eq5
        # Calculation is in Fahrenheit

        # The Rothfusz regression is not valid for extreme temperature and
        # relative humidity conditions beyond the range of data considered by Steadman.

        # Rothfusz regression
        c1 = -42.379
        c2 =   2.04901523
        c3 =  10.14333127
        c4 =  -0.22475541
        c5 =  -0.00683783
        c6 =  -0.05481717
        c7 =   0.00122874
        c8 =   0.00085282
        c9 =  -0.00000199
    
        T = result['temp_F']
        R = result['humidity']
        Tsq = T * T
        Rsq = R * R

        hi = (c1 + (c2 * T) + (c3 * R) + (c4 * T * R) + (c5 * Tsq)
                + (c6 * Rsq) + (c7 * Tsq * R) + (c8 * T * Rsq) + (c9 * Tsq * Rsq))

        if T <= 112 and R < 13:
            hi -= ((13 - R) / 4) * sqrt((17 - fabs(T - 95.0)) / 17)
            # hi -= (3.25 - 0.25 * R) * sqrt(1 - (fabs(T - 95) / 17))
        if T <= 87 and R > 85:
            hi += ((R - 85) / 10) * ((87 - T) / 5)
            # hi += (0.1 * R - 8.5) * (17.4 - 0.2 * T)

        return hi

    if temp_C >= 26.67:
        result['heatIndex_F'] = heat_index()
        output.append('HeatIndex: %.2f °F; ' % result['heatIndex_F'])
    else:
        print('Not warm enough (less than 80.1 °F) for Heat Index')
        result['heatIndex_F'] = result['temp_F']
    
    # Battery Voltage
    # Voltage Divider R1 = 220k+100k+220k = 540K and R2 = 100k
    
    # esp8266
    adc = ADC(0)
    raw = adc.read()
    result['volt'] = raw * calib_factor / 1024 # esp8266

    # # esp32
    # ADC_PIN = 36
    # # adc = ADC(ADC_PIN, atten=ADC.ATTN_11DB)
    # adc = ADC(ADC_PIN)
    # raw = adc.read_uv()
    # result['volt'] = raw / 1000000 * calib_factor # esp32
    
    output.append('Voltage: %.2f V; ' % result['volt'])

    del bme
    del sys.modules['bme280_int']
    
    # from moisture import take_moisture
    # moisture_reading = take_moisture(i2c=i2c)
    # # result['moisture'] = moisture_reading[0]
    # result['moisture'] = moisture_reading
    
    # # output.append('Moisture value: %s; Moisture Voltage: %s V\n' %
    # #               (moisture_reading[0], moisture_reading[1]))
    # output.append('Moisture value: %s' % moisture_reading)

    print(''.join(output))
    
    # round floats to 2 decimal places
    result = dict(zip(result, map(lambda x: round(x, 2) if isinstance(x, float) else x, result.values())))

    # del take_moisture
    # del sys.modules['moisture']

    return result
