import sys, gc

def GatherData():
    import weather_station
    result = weather_station.main()
    del sys.modules['weather_station']
    gc.collect()

    return result

def SendThingspeak(host, api_key, channel_id, data):
    import send_thingspeak
    send_thingspeak.SendToThingspeak(host, api_key, channel_id, data)
    del sys.modules['send_thingspeak']
    gc.collect()

def SendBlynk(blynk_auth, data):
    import send_blynk
    send_blynk.SendToBlynk(blynk_auth, data)
    del sys.modules['send_blynk']
    gc.collect()

def SendMQTT(mqtt_conf, data):
    import send_mqtt
    paused = send_mqtt.SendToMQTT(mqtt_conf, data)
    del sys.modules['send_mqtt']
    gc.collect()

    return paused

def main():
    from cycle_machine import GoToSleep
    from machine import RTC
    
    result = GatherData()

    print('Free mem after W.S. unloaded in main(): %d' % gc.mem_free())

    if result['apps']['thingspeak']['enabled']:
        SendThingspeak(result['apps']['thingspeak']['host'],
                    result['apps']['thingspeak']['api_key'],
                    result['apps']['thingspeak']['channel_id'],
                    result['values'])

    if result['apps']['blynk']['enabled']:
        SendBlynk(result['apps']['blynk']['auth'],
                result['values'])

    if result['apps']['mqtt']['enabled']:
        paused = SendMQTT(result['apps']['mqtt'],
                        result['values'])

    rtc = RTC()
    rtc.memory(rtc.memory()[:-1] + '1')
    
    if not paused:
        GoToSleep(result['sleep_time_secs'])
    else:
        import sys
        sys.exit()

main()
