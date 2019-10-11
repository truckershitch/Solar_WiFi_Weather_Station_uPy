import sys, gc

def GatherData():
    import weather_station
    result = weather_station.main()
    del sys.modules['weather_station']
    gc.collect()

    return result

def SendThingspeak(host, api_key, data):
    import send_thingspeak
    send_thingspeak.SendToThingspeak(host, api_key, data)
    del sys.modules['send_thingspeak']
    gc.collect()

def SendBlynk(blynk_auth, data):
    import send_blynk
    send_blynk.SendToBlynk(blynk_auth, data)
    del sys.modules['send_blynk']
    gc.collect()

def SendMQTT(CONF, data):
    import send_mqtt
    paused = send_mqtt.SendToMQTT(CONF, data)
    del sys.modules['send_mqtt']
    gc.collect()

    return paused

def WriteTimestamp(logfile, timestamp):
    f = open(logfile, 'w')
    f.write('%d\n' % timestamp)
    f.close()

def main():
    from cycle_machine import GoToSleep
    
    result = GatherData()

    print('Free mem after W.S. unloaded in main(): %d' % gc.mem_free())

    if result['apps']['thingspeak']['enabled']:
        SendThingspeak(result['apps']['thingspeak']['host'],
                    result['apps']['thingspeak']['api_key'],
                    result['values'][:8])

    if result['apps']['blynk']['enabled']:
        SendBlynk(result['apps']['blynk']['auth'],
                result['values'])

    if result['apps']['mqtt']['enabled']:
        paused = SendMQTT(result['apps']['mqtt'],
                        result['values'])

    WriteTimestamp(result['verify_file'],
                result['timestamp'])
    
    if not paused:
        GoToSleep(result['sleep_time_secs'])
    else:
        import sys
        sys.exit()

if __name__ == '__main__':
    main()