# Solar Wifi Weather Station
# Very alpha at this stage
# Last updated October 19, 2019
#
# This is heavily based on 3KUdelta's Solar WiFi Weather Station.
# There was much cutting and pasting!
# See https://github.com/3KUdelta/Solar_WiFi_Weather_Station
# This in turn was based on the work of Open Green Energy:
# https://www.instructables.com/id/Solar-Powered-WiFi-Weather-Station-V20/
# Everyone has done very solid work!  I am impressed!
#
# I wanted to be able to update the code over WiFi and watch the serial
# output on my machine locally, thus MicroPython.
# It also helps me hone my craft, whatever little I have :)
#

VERSION = '0.5.0'

import time, sys, gc

# DST CALCULATION
SECS_IN_DAY = 86400
SECS_IN_HOUR = 3600
DST_ADJ_AMT = 0                 # Amount of seconds to adjust for seasonal time change
                                # See dst_us.json for sample configuration
curr_dst_status = 0             # Currrent DST Status -- 0 = Winter, 1 = Summer
saved_dst_status = 0            # DST Status stored in SPIFFS

# FORECAST CALCULATION
current_timestamp = 0           # Actual timestamp read from NTPtime
saved_timestamp = 0             # Timestamp stored in SPIFFS

# FORECAST RESULT
accuracy = 0                    # Counter, if enough values for accurate forecasting

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

def MeasurementEvent(CONF_WEATHER):
    import measurement

    result = measurement.TakeMeasurement(CONF_WEATHER)
    
    del sys.modules['measurement']
    gc.collect()

    return result

def FirstTimeRun(CONF_FILE, rel_Pres_Rounded_hPa):
    from cycle_machine import ResetMachine

    global accuracy

    print('---> Starting initialization process')
    accuracy = 1
    try:
        myDataFile = open(CONF_FILE['DATAFILE'], 'w')
    except:
        print('ERROR: Failed to open datafile.')
        print('Stopping process - there is an OS problem here.')
        sys.exit()

    myDataFile.write('%d\n%d\n%d\n%d\n'
                      % (current_timestamp,
                         curr_dst_status,
                         accuracy,
                         current_timestamp))
    for _ in range(12):
        myDataFile.write('%d\n' % rel_Pres_Rounded_hPa)
    print('*** Saved initial pressure data. ***')
    myDataFile.close()

    myDataFile = open(CONF_FILE['VERIFYFILE'], 'w')
    myDataFile.write('%d\n' % current_timestamp)
    myDataFile.close()

    print('Doing a reset now.')
    ResetMachine()
    
def VerifyLastRunCompleted(verify_ts, VERIFYFILE, ERRORFILE):
    f = open(VERIFYFILE, 'r')
    last_ts = int(f.readline())
    f.close()

    if last_ts != verify_ts:
        import machine

        f = open(ERRORFILE, 'a+')
        f.write('Reset after %s\tCause: %s\n'
                % (FmtDateTime(verify_ts), machine.reset_cause()))
        f.close()

def ReadDataFile(CONF_FILE, rel_Pres_Rounded_hPa):
    global saved_dst_status, saved_timestamp, accuracy

    try:
        myDataFile = open(CONF_FILE['DATAFILE'], 'r')
    except:
        print('Failed to open file for reading -- assuming First Run')
        FirstTimeRun(CONF_FILE, rel_Pres_Rounded_hPa)
    
    print('---> Now reading from ESP8266')

    saved_timestamp  = int(myDataFile.readline())
    saved_dst_status = int(myDataFile.readline())
    accuracy         = int(myDataFile.readline())
    verifier         = int(myDataFile.readline())
    
    VerifyLastRunCompleted(verifier, CONF_FILE['VERIFYFILE'], CONF_FILE['ERRORFILE'])

    print('Saved Timestamp: %d\nSaved DST Status: %d\nSaved Accuracy Value: %d'
          % (saved_timestamp, saved_dst_status, accuracy))

    pressure_value = []
    for _ in range(12):
        pval = int(myDataFile.readline())
        pressure_value.append(pval)
    print('Last 12 saved pressure values:', ('%d; ' * 12)[:-2] % tuple(pressure_value))

    myDataFile.close()

    return pressure_value

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

def WriteDataFile(write_timestamp, DATAFILE, pressure_value):
    try:
        myDataFile = open(DATAFILE, 'w')
        print('---> Now writing to ESP8266')

        myDataFile.write('%d\n%d\n%d\n%d\n'
                          % (write_timestamp,
                             curr_dst_status,
                             accuracy,
                             current_timestamp))
        for value in pressure_value:
            myDataFile.write('%d\n' % value)
        
        myDataFile.close()

    except:
        print('ERROR: Failure writing to data file!')
        sys.exit()

def ZambrettiPrediction(LANGUAGE, rel_Pres_Rounded_hPa, pressure_value):
    import zambretti

    month = time.localtime(current_timestamp)[1]
    
    prediction = zambretti.MakePrediction(
                        LANGUAGE,
                        rel_Pres_Rounded_hPa,
                        pressure_value,
                        accuracy,
                        month)

    del sys.modules['zambretti']
    gc.collect()
    
    return prediction

def main():
    global accuracy
    
    pressure_value = [] # holds 12 pressure values in hPa (6 hours data, [0] most recent)

    print('Start of Solar WiFi Weather Station %s' % VERSION)
    print('Free mem: %d' % gc.mem_free())

    CONF = LoadConfig()

    ConnectWiFi(CONF['wifi'], CONF['other']['SLEEP_TIME_MIN'], CONF['file']['ERRORFILE'])

    ConfigureTime(CONF['time'], CONF['other']['SLEEP_TIME_MIN'], CONF['file']['ERRORFILE'])

    result = MeasurementEvent(CONF['weather']) #acquire sensor data

    pressure_value = ReadDataFile(CONF['file'], result['rel_Pres_Rounded_hPa']) #read stored values and update data if more recent data is available

    if CONF['time']['DST']['USE_DST']:
        dst_adjustment = CheckForTimeChange()
    else:
        dst_adjustment = 0

    ts_diff = current_timestamp - saved_timestamp + dst_adjustment
    print('Timestamp difference: %s' % ts_diff)

    if ts_diff >= 6 * SECS_IN_HOUR:
        FirstTimeRun(CONF['file'], result['rel_Pres_Rounded_hPa'])
    elif ts_diff >= SECS_IN_HOUR / 2:
        # prepend list with new pressure value and move it right one notch
        pressure_value = [result['rel_Pres_Rounded_hPa']] + pressure_value[:-1]

        if accuracy < 12:
            accuracy += 1
        
        WriteDataFile(current_timestamp, CONF['file']['DATAFILE'], pressure_value)
    else:
        WriteDataFile(saved_timestamp + dst_adjustment, CONF['file']['DATAFILE'], pressure_value)

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
