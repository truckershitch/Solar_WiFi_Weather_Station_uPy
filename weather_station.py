# Solar Wifi Weather Station
# Beta stage
# Last updated July 17, 2023
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
# 2023-05-29 -- Added Moisture readings
# 2023-06-23 -- Refactored function arguments, error handling
# 2023-07-01 -- Fixed error in main()
#   -- fixed timestamp condition
#   -- WriteRTCMemory() was badly indented and not called
# 2023-07-02 -- switched back to ntptime (slightly modified)

VERSION = '0.21.1'
MOD_DATE = 'July 28, 2023'

import time, sys, gc
from errorwrapper import ErrorWrapper

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

# MOISTURE MEASUREMENT
last_mval_timestamp = 0      # Timestamp of last recorded moisture value
                             # in RTC memory
mval_count          = 12     # Number of moisture values (every 2 hours for 24 hours)

e_wrap = ErrorWrapper('error.log', sleep_mins=10)

# END GLOBAL VARIABLES

def LoadConfig():
    import json

    f = open('config_ws.json', 'r')
    return json.loads(f.read())

def ConnectWiFi(CONF_WIFI):
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
                print('No WiFi. Throwing CustomNetworkError.')
                e_wrap.sleep_it_off(exc='No WiFi', mins=5)
                                         
            time.sleep(1)
    print('network config:', sta_if.ifconfig())

def SetNTPTime(NTP_HOSTS):
    import new_ntp

    print('Now setting clock with NTP server')
    time_is_set = False
    count = 0
    while not time_is_set:
        print('.', end='')
        time_is_set = new_ntp.settime(NTP_HOSTS[count])

        if time_is_set:
            print('Set time successfully.')
        time.sleep(1)
        count += 1
        if count == len(NTP_HOSTS):
            print('Could not connect to NTP server')
            e_wrap.sleep_it_off(exc='Could not connect to NTP server', mins=5)

    del sys.modules['new_ntp']
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

def ConfigureTime(CONF_TIME):
    global current_timestamp

    SetNTPTime(CONF_TIME['NTP_HOSTS'])
    current_timestamp = time.time() + CONF_TIME['TZ'] * SECS_IN_HOUR
    if CONF_TIME['DST']['USE_DST']:
        CheckForSummerTime(CONF_TIME['DST']['COUNTRY'])

    print('Current UNIX timestamp: %d\nDST Status: %d\nDate & Time: %s'
          % (current_timestamp, curr_dst_status, FmtDateTime(current_timestamp)))

def ReadSensors(CONF_WEATHER, batt_calib):
    import measurement

    result = measurement.TakeMeasurement(CONF_WEATHER, batt_calib)

    del sys.modules['measurement']
    gc.collect()

    return result

def FirstRun(rel_Pres_Rounded_hPa, moisture_reading):
    import machine

    global accuracy

    print('---> Starting initialization process')
    rtc = machine.RTC()
    accuracy = 1

    data = '%d,%d,%d,%d,' % (current_timestamp,
                             current_timestamp,
                             curr_dst_status,
                             accuracy)

    for _ in range(pval_count):
        data += '%d,' % rel_Pres_Rounded_hPa
    print('---> Saved initial pressure data')
    # for _ in range(mval_count):
    #     data += '%d,' % moisture_reading
    # for _ in range(mval_count):
    #     data += '%d,' % int(reading[1] * 1000)
    data += '%d,' % moisture_reading # just one
    print('---> Saved initial moisture data')
    data += '1'

    rtc.memory(data)

    print('Calling machine.reset()')
    machine.reset()

def ReadRTCMemory(rel_Pres_Rounded_hPa, moisture_reading):
    from machine import RTC

    global saved_dst_status, last_pval_timestamp, last_mval_timestamp, accuracy

    rtc = RTC()

    print('---> Now reading ESP8266 RTC memory')
    data = rtc.memory()
    print('Raw RTC memory data:\n%s\n' % data)

    if not data:
        print('Empty RTC memory -- calling FirstRun()')
        FirstRun(rel_Pres_Rounded_hPa, moisture_reading)

    data_list = [int(i) for i in data.split(b',')]

    last_pval_timestamp = data_list[0]
    last_mval_timestamp = data_list[1]
    saved_dst_status    = data_list[2]
    accuracy            = data_list[3]
    flag                = data_list[:-1]

    stat_data_count = 4

    if not flag:
        # Last run incomplete. Fix stats and go on
        last_pval_timestamp = current_timestamp
        last_mval_timestamp = current_timestamp

        data_list = [
            current_timestamp,
            current_timestamp,
            saved_dst_status,
            accuracy
        ] + data_list[stat_data_count:]

    pressure_values = []
    for i in range(
        stat_data_count,
        stat_data_count + pval_count
    ):
        pressure_values.append(int(data_list[i]))
    print('Last %d saved pressure values:' % pval_count,
             ('%d; ' * pval_count)[:-2] % tuple(pressure_values))

    moisture_values = []
    for i in range(
        stat_data_count + pval_count,
        # stat_data_count + pval_count + mval_count
        len(data_list) - 1
    ):
        moisture_values.append(int(data_list[i]))
    mvals_saved = len(moisture_values)
    print('Last %d saved moisture values:' %
        mvals_saved, ('%d; ' * mvals_saved)[:-2] % tuple(moisture_values))

    return (pressure_values, moisture_values)

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

def WriteRTCMemory(p_write_timestamp, pressure_value, m_write_timestamp, moisture_value):
    from machine import RTC

    rtc = RTC()
    print('\n---> Now writing to ESP8266 RTC memory')

    data = '%d,%d,%d,%d,' % (p_write_timestamp,
                            m_write_timestamp,
                            curr_dst_status,
                            accuracy)

    for val in pressure_value:
        data += '%d,' % val
    for val in moisture_value:
        data += '%d,' % val
    data += '0' # flag as unverified

    rtc.memory(data)

    print('Wrote:\n"%s"\nto RTC memory\n' % data)

def ZambrettiPrediction(Z_DATA, rel_Pres_Rounded_hPa, pressure_value):
    import zambretti

    month = time.localtime(current_timestamp)[1]

    prediction = zambretti.MakePrediction(
                        Z_DATA,
                        rel_Pres_Rounded_hPa,
                        pressure_value,
                        accuracy,
                        month)

    del sys.modules['zambretti']
    gc.collect()

    return prediction

def MoistureWeightedAverage(FACTOR_MAX, FACTOR_MIN, moisture_data):
    # weighted moisture average
    weights = [round(FACTOR_MAX - i * (FACTOR_MAX - FACTOR_MIN) / (mval_count - 1), 2) for i in range(mval_count)]
    wt_avg_num = sum([moisture_data[i] * weights[i] for i in range(len(moisture_data))])
    wt_avg_denom = sum(weights[:len(moisture_data)]) # could be sum(weights)
    moisture_avg = round(wt_avg_num / wt_avg_denom, 2)

    return moisture_avg

def main():
    from errorwrapper import ErrorWrapper

    global accuracy, e_wrap

    pressure_value = [] # pressure values in hPa (1 per half hour, [0] most recent)
    moisture_value = [] # raw moisture values every 2 hours

    print('Start of Solar WiFi Weather Station %s' % VERSION)
    print('Last modified %s' % MOD_DATE)
    print('Free mem: %d' % gc.mem_free())

    CONF = e_wrap.wrap(LoadConfig)

    e_wrap.wrap(ConnectWiFi, CONF['wifi'])
    e_wrap.wrap(ConfigureTime, CONF['time'])
    e_wrap.set_ts(current_timestamp)

    #acquire sensor data
    result = e_wrap.wrap(ReadSensors, CONF['weather'], CONF['other']['BATT_CALIB'])
    if result is None:
        e_wrap.call_reset(exc='Error reading sensors. Check hardware! Calling reset')        
    elif result['moisture'] <= 0:
        e_wrap.sleep_it_off(exc='Moisture reading: %s.  Sleeping' % result['moisture'], mins=3)
        # e_wrap.call_reset(exc='Moisture reading: %s. Calling reset' % result['moisture'])

    (pressure_value, moisture_value) = e_wrap.wrap(
        ReadRTCMemory,
        result['rel_Pres_Rounded_hPa'],
        result['moisture']
    )

    if CONF['time']['DST']['USE_DST']:
        dst_adjustment = e_wrap.wrap(CheckForTimeChange)
    else:
        dst_adjustment = 0

    p_ts_diff = current_timestamp - last_pval_timestamp + dst_adjustment
    p_m, p_s = divmod(p_ts_diff, 60)
    p_h, p_m = divmod(p_m, 60)
    print(f'Pressure Timestamp difference: {p_ts_diff:d} secs or {p_h:d}:{p_m:02d}:{p_s:02d}')

    m_ts_diff = current_timestamp - last_mval_timestamp + dst_adjustment
    m_m, m_s = divmod(m_ts_diff, 60)
    m_h, m_m = divmod(m_m, 60)
    print(f'Moisture Timestamp difference: {m_ts_diff:d} secs or {m_h:d}:{m_m:02d}:{m_s:02d}')

    time_limit_p = SECS_IN_HOUR // 2 # 30 mins
    time_limit_m = SECS_IN_HOUR * CONF['other']['WT_AVG_HOURS']
    take_p = p_ts_diff >= time_limit_p
    take_m = m_ts_diff >= time_limit_m
    flush_p = p_ts_diff >= SECS_IN_HOUR * 2
    flush_m = m_ts_diff >= SECS_IN_HOUR * mval_count * CONF['other']['WT_AVG_HOURS'] / 4 # rough calculation
    p_tstamp = current_timestamp if take_p else last_pval_timestamp + dst_adjustment
    m_tstamp = current_timestamp if take_m else last_mval_timestamp + dst_adjustment

    if take_p:
        tlp_m, tlp_s = divmod(time_limit_p, 60)
        tlp_h, tlp_m = divmod(tlp_m, 60)
        print(f'Pressure Time difference longer than {tlp_h:d}:{tlp_m:02d}:{tlp_s:02d}')
        print('Recording pressure value of %s in RTC Memory' % result['rel_Pres_Rounded_hPa'])
    if take_m:
        tlm_m, tlm_s = divmod(time_limit_m, 60)
        tlm_h, tlm_m = divmod(tlm_m, 60)
        print(f'Moisture Time difference longer than {tlm_h:d}:{tlm_m:02d}:{tlm_s:02d}')
        print('Recording moisture value of %s in RTC Memory' % result['moisture'])
    
    if flush_p or flush_m:
        if flush_p:
            print('More than 2 hours since last pressure reading!')
            print('Flushing pressure_value list')
            # reset pressure_value
            pressure_value = [result['rel_Pres_Rounded_hPa'] for _ in range(pval_count)]

        if flush_m:
            print('More than  since last moisture reading!')
            print('Flushing moisture value list')
            # reset moisture_value
            moisture_value = [result['moisture']]

    elif take_p or take_m: # take pressure or moisture reading
        # pressure
        if take_p:
            # prepend list with new pressure value and remove one value from end
            pressure_value = [result['rel_Pres_Rounded_hPa']] + pressure_value[:-1]

            if accuracy < pval_count:
                accuracy += 1

        # moisture
        if take_m:
            moisture_reading = result['moisture']
            moisture_value = [moisture_reading] + moisture_value
            if len(moisture_value) > mval_count:
                moisture_value = moisture_value[:-1]
            ## moisture_value = [int(moisture_voltage * 1000)] + moisture_value[:-1]

    # write data to RTC memory
    e_wrap.wrap(
        WriteRTCMemory,
        p_tstamp,
        pressure_value,
        m_tstamp,
        moisture_value
    )

    # make sure  we record on the interval
    interval = CONF['other']['SLEEP_TIME_MIN'] * 60
    diff_from_half_hour = SECS_IN_HOUR / 2 - p_ts_diff

    if diff_from_half_hour >= 0:
        if diff_from_half_hour >= interval:
            sleep_time_secs = interval
        else:
            sleep_time_secs = diff_from_half_hour
    else:
        sleep_time_secs = interval

    (ZambrettisWords,
     trend_in_words,
     accuracy_in_percent) = e_wrap.wrap(ZambrettiPrediction,
                                   CONF['weather']['ZAMBRETTI'],
                                   result['rel_Pres_Rounded_hPa'],
                                   pressure_value)

    moisture_avg = e_wrap.wrap(
        MoistureWeightedAverage,
        CONF['other']['WT_AVG_FACTOR_MAX'],
        CONF['other']['WT_AVG_FACTOR_MIN'],
        moisture_value
    )

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
            result['moisture'],
            moisture_avg,
            accuracy_in_percent,
            ZambrettisWords,
            trend_in_words
        ],
        'sleep_time_secs': sleep_time_secs # need this in one place
    }

    print('\nMoisture Reading: %.2f' % result['moisture'])
    print('Moisture Average: %.2f' % moisture_avg)
    print('Battery Voltage: %s' % result['volt'])

    del CONF
    del result
    del pressure_value
    del moisture_value
    del e_wrap

    gc.collect() # take out the garbage
    print('\nFree mem when leaving weather_station: %d' % gc.mem_free())

    return package
