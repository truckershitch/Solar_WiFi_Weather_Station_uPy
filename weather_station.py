# Solar Wifi Weather Station
# Beta stage
# Last updated April 28, 2020
#
# This is heavily based on 3KUdelta's Solar WiFi Weather Station.
# There was much cutting and pasting!
# See https://github.com/3KUdelta/Solar_WiFi_Weather_Station
# This in turn was based on the work of Open Green Energy:
# https://www.instructables.com/id/Solar-Powered-WiFi-Weather-Station-V20/
# Everyone has done very solid work!  I am impressed!
#
# I wanted to be able to update the code over WiFi and watch
# the serial output on my machine locally, thus MicroPython.
# It also helps me hone my craft, whatever little I have :)
#
# 2020-04-28
# Changed storage of Zambretti data to RTC memory to avoid
# wearing out flash memory with writes and rewrites.
# Errors are still logged to flash but maybe this is
# unnecessary.
# 2020-05-23
# Changed Zambretti forecast period to 3 hours.

VERSION = '0.7.0'

import time, sys, gc

# DST CALCULATION            # See dst_us.json for sample configuration
SECS_IN_DAY         = 86400
SECS_IN_HOUR        = 3600
DST_ADJ_AMT         = 0      # Amount of seconds to adjust for seasonal
                             # time change.  Calculated in dst.py and
                             # configured in dst_your_country.json

curr_dst_status     = 0      # Currrent DST Status
                             # 0 = Winter, 1 = Summer
saved_dst_status    = 0      # DST Status stored in RTC memory

# FORECAST CALCULATION
current_timestamp   = 0      # Timestamp read from NTPtime
last_pval_timestamp = 0      # Timestamp of last recorded pressure value
                             # in RTC memory
pval_count          = 6      # Number of pressure values
accuracy            = 0      # Accuracy counter for forecasting

# END GLOBAL VARIABLES

def LoadConfig():
    import json

    f = open('config.json', 'r')
    return json.loads(f.read())

def ConnectWiFi(CONF_WIFI, SLEEP_TIME_MIN, ERRORFILE):
    import network

    sta_if = network.WLAN(network.STA_IF)
    ap_if = network.WLAN(network.AP_IF)

    ap_if.active(False)

    if not sta_if.isconnected():
        print('Connecting to network...')
        sta_if.active(True)
        sta_if.connect(CONF_WIFI['ssid'], CONF_WIFI['pass'])
        count = 0
        while not sta_if.isconnected():
            count += 1
            print('.', end='')
            if count == 15:
                from cycle_machine import GoToSleep
                print('Could not connect.  Taking a nap.')
                GoToSleep(SLEEP_TIME_MIN * 60, ERRORFILE, 'Could not connect to network.')
            time.sleep(1)
    print('network config:', sta_if.ifconfig())

def SetNTPTime(NTP_HOSTS, SLEEP_TIME_MIN, ERRORFILE):
    import sntp # modified ntptime

    print('Now setting clock with NTP server')
    time_is_set = False
    count = 0
    while not time_is_set:
        print('.', end='')
        time_is_set = sntp.settime(NTP_HOSTS)
        if time_is_set:
            print('Set time successfully.')
        time.sleep(1)        
        count += 1
        if count == 5:
            from cycle_machine import GoToSleep
            print('Could not connect to NTP Server!\nSleeping...')
            GoToSleep(SLEEP_TIME_MIN * 60, ERRORFILE, 'Could not connect to NTP Server.')

    del sys.modules['sntp']
    gc.collect()

def CheckForSummerTime(COUNTRY):
    global curr_dst_status, current_timestamp, DST_ADJ_AMT
    
    import dst

    (curr_dst_status, 
     current_timestamp,
     DST_ADJ_AMT)        = dst.SummerTimeAdjustment(COUNTRY,
                                                    current_timestamp)

    del sys.modules['dst']
    gc.collect()

def FmtDateTime(timestamp):
    t = time.localtime(timestamp)
    fmt = '%02d/%02d/%04d %02d:%02d:%02d'
    return fmt % (t[1], t[2], t[0], t[3], t[4], t[5])

def ConfigureTime(CONF_TIME, SLEEP_TIME_MIN, ERRORFILE):
    global current_timestamp

    SetNTPTime(CONF_TIME['NTP_HOSTS'], SLEEP_TIME_MIN, ERRORFILE)
    current_timestamp = time.time() + CONF_TIME['TZ'] * SECS_IN_HOUR
    if CONF_TIME['DST']['USE_DST']:
        CheckForSummerTime(CONF_TIME['DST']['COUNTRY'])

    print('Current UNIX timestamp: %d\nDST Status: %d\nDate & Time: %s'
          % (current_timestamp, curr_dst_status, FmtDateTime(current_timestamp)))

def MeasurementEvent(CONF_WEATHER, batt_calib):
    import measurement

    result = measurement.TakeMeasurement(CONF_WEATHER, batt_calib)
    
    del sys.modules['measurement']
    gc.collect()

    return result

def FirstTimeRun(rel_Pres_Rounded_hPa):
    from cycle_machine import ResetMachine
    from machine import RTC

    global accuracy

    print('---> Starting initialization process')
    rtc = RTC()
    accuracy = 1

    data = '%d,%d,%d,%d,' % (current_timestamp,
                             curr_dst_status,
                             accuracy,
                             current_timestamp)
    for _ in range(pval_count):
        data += '%d,' % rel_Pres_Rounded_hPa
    print('---> Saved initial pressure data')
    data += '1'

    rtc.memory(data)
    
    print('Doing a reset now.')
    ResetMachine()

def VerifyLastRunCompleted(flag, timestamp, ERRORFILE):
    if not flag:
        import machine
        from cycle_machine import WriteError

        WriteError(ERRORFILE, 'Reset cause: %s'
                % machine.reset_cause(), timestamp)

def ReadRTCMemory(ERRORFILE, rel_Pres_Rounded_hPa):
    from machine import RTC

    global saved_dst_status, last_pval_timestamp, accuracy

    rtc = RTC()

    print('---> Now reading ESP8266 RTC memory')
    data = rtc.memory()
    
    if not data:
        print('Empty RTC memory -- assuming First Run')
        FirstTimeRun(rel_Pres_Rounded_hPa)

    data_list = [int(i) for i in data.split(b',')]

    last_pval_timestamp = data_list[0]
    saved_dst_status    = data_list[1]
    accuracy            = data_list[2]
    last_run_timestamp  = data_list[3]
    flag                = data_list[:-1]    

    VerifyLastRunCompleted(flag, last_run_timestamp, ERRORFILE)

    pressure_values = []
    for i in range(4, pval_count + 4):
        pressure_values.append(data_list[i])
    print('Last %d saved pressure values:' % pval_count,
             ('%d; ' * pval_count)[:-2] % tuple(pressure_values))

    return pressure_values

def CheckForTimeChange():
    # Has the time just changed?
    # Return adjustment to time difference calculation in seconds

    if curr_dst_status != saved_dst_status:
        if curr_dst_status: # Switch to Summer Time
            return DST_ADJ_AMT
        else: # Switch to Daylight Saving Time
            return -DST_ADJ_AMT
    else:
        return 0

def WriteRTCMemory(write_timestamp, pressure_value):
    from machine import RTC

    rtc = RTC()
    print('---> Now writing to ESP8266 RTC memory')
    
    data = '%d,%d,%d,%d,' % (write_timestamp,
                            curr_dst_status,
                            accuracy,
                            current_timestamp)
    for val in pressure_value:
        data += '%d,' % val
    data += '0' # flag as unverified

    rtc.memory(data)

def ZambrettiPrediction(LANGUAGE, Z_DATA, rel_Pres_Rounded_hPa, pressure_value):
    import zambretti

    month = time.localtime(current_timestamp)[1]
    
    prediction = zambretti.MakePrediction(
                        LANGUAGE,
                        Z_DATA,
                        rel_Pres_Rounded_hPa,
                        pressure_value,
                        accuracy,
                        month)

    del sys.modules['zambretti']
    gc.collect()
    
    return prediction

def main():
    global accuracy
    
    pressure_value = [] # pressure values in hPa (1 per half hour, [0] most recent)

    print('Start of Solar WiFi Weather Station %s' % VERSION)
    print('Free mem: %d' % gc.mem_free())

    CONF = LoadConfig()

    ConnectWiFi(CONF['wifi'], CONF['other']['SLEEP_TIME_MIN'], CONF['file']['ERRORFILE'])

    ConfigureTime(CONF['time'], CONF['other']['SLEEP_TIME_MIN'], CONF['file']['ERRORFILE'])

    #acquire sensor data
    result = MeasurementEvent(CONF['weather'], CONF['other']['BATT_CALIB'])

    #read stored values and update data if more recent data is available
    pressure_value = ReadRTCMemory(CONF['file']['ERRORFILE'], result['rel_Pres_Rounded_hPa'])

    if CONF['time']['DST']['USE_DST']:
        dst_adjustment = CheckForTimeChange()
    else:
        dst_adjustment = 0

    ts_diff = current_timestamp - last_pval_timestamp + dst_adjustment
    print('Timestamp difference: %s' % ts_diff)

    if ts_diff >= pval_count / 2 * SECS_IN_HOUR:
        FirstTimeRun(result['rel_Pres_Rounded_hPa'])
    elif ts_diff >= SECS_IN_HOUR / 2:
        # prepend list with new pressure value and move it right one notch
        pressure_value = [result['rel_Pres_Rounded_hPa']] + pressure_value[:-1]

        if accuracy < pval_count:
            accuracy += 1
        
        WriteRTCMemory(current_timestamp, pressure_value)
    else:
        WriteRTCMemory(last_pval_timestamp + dst_adjustment, pressure_value)

    # make sure  we record on the half hour
    interval = CONF['other']['SLEEP_TIME_MIN'] * 60
    diff_from_half_hour = SECS_IN_HOUR / 2 - ts_diff

    if diff_from_half_hour >= 0:
        if diff_from_half_hour >= interval:
            sleep_time_secs = interval
        else:
            sleep_time_secs = diff_from_half_hour
    else:
        sleep_time_secs = interval

    (ZambrettisWords,
     trend_in_words,
     accuracy_in_percent) = ZambrettiPrediction(CONF['other']['LANGUAGE'],
                                                CONF['weather']['ZAMBRETTI'],
                                                result['rel_Pres_Rounded_hPa'],
                                                pressure_value)

    package = {
        'values':[
            result['temp_F'],
            result['humidity'],
            result['dewPt_F'],
            result['dewPtSpread_F'],
            result['heatIndex_F'],
            result['measured_Pres_inHg'],
            result['rel_Pres_inHg'],
            result['volt'],
            accuracy_in_percent,
            ZambrettisWords,
            trend_in_words
        ],
        'apps': CONF['apps'],
        'sleep_time_secs': sleep_time_secs,
        'verify_file': CONF['file']['VERIFYFILE'],
        'error_file': CONF['file']['ERRORFILE'],
        'timestamp': current_timestamp
    }

    del CONF
    del result
    del pressure_value

    gc.collect() # take out the garbage
    print('Free mem when leaving weather_station: %d' % gc.mem_free())

    return package
