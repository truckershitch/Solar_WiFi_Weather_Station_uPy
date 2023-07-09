from errorwrapper import ErrorWrapper
import sys, gc

w = ErrorWrapper('error.log')

def GatherData():
    import weather_station

    print('Not errorwrapping weather_station')
    result = weather_station.main()

    # print('Errorwrapping weather_station')
    # result = w.wrap(weather_station.main) # double wrap?
    
    del sys.modules['weather_station']
    gc.collect()

    return result

def SendThingspeak(host, user, api_key, channel_id, data):
    import send_thingspeak
    w.wrap(send_thingspeak.SendToThingspeak, host, user, api_key, channel_id, data)

    del sys.modules['send_thingspeak']
    gc.collect()

def SendBlynk(blynk_auth, data):
    import send_blynk
    w.wrap(send_blynk.SendToBlynk, blynk_auth, data)

    del sys.modules['send_blynk']
    gc.collect()

def SendMQTT(mqtt_conf, data):
    import send_mqtt
    paused = w.wrap(send_mqtt.SendToMQTT, mqtt_conf, data)
    
    del sys.modules['send_mqtt']
    gc.collect()

    return paused

def LoadConfig():
    import json

    f = open('config_main.json', 'r')
    return json.loads(f.read())

def main():
    from cycle_machine import GoToSleep
    from machine import RTC

    CONF = LoadConfig()
    
    result = GatherData()

    print('Free mem after W.S. unloaded in main(): %d\n' % gc.mem_free())

    if CONF['apps']['thingspeak']['enabled']:
        SendThingspeak(CONF['apps']['thingspeak']['host'],
                    CONF['apps']['thingspeak']['user'],
                    CONF['apps']['thingspeak']['api_key'],
                    CONF['apps']['thingspeak']['channel_id'],
                    result['values'])

    if CONF['apps']['blynk']['enabled']:
        SendBlynk(CONF['apps']['blynk']['auth'],
                result['values'])

    if CONF['apps']['mqtt']['enabled']:
        paused = SendMQTT(CONF['apps']['mqtt'],
                        result['values'])

    # Verify run completed in RTC
    rtc = RTC()
    rtc.memory(rtc.memory()[:-1] + '1')
    
    if not paused:
        GoToSleep(result['sleep_time_secs'])
    else:
        import sys
        sys.exit()

main()
