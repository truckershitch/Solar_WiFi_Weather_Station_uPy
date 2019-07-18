def SendToThingspeak(host, api_key, result):
    import gc
    from urllib.urequest import urlopen

    def create_url():
        url = ('https://%s/update?api_key=%s' % (host, api_key) +
              ''.join(['&field%d=%.2f' % (x +1, result[x]) for x in range(len(result))]))
        return url
    
    try:
        res = urlopen(url=create_url())
        print('Response: %s\nData sent to Thingspeak' % res.read())
    except:
        print('Send to Thingspeak failed')
    
    # for i, value in enumerate(result):
    #     data = 'field%d=%.2f' % (i + 1, value)
        
    #     res = urequests.post(url='https://%s/update' % host,
    #                         headers= {
    #                             'X-THINGSPEAKAPIKEY': api_key,
    #                             'Content-Type': 'application/x-www-form-urlencoded'
    #                         },
    #                         data=data)
    #     del data
    #     if res.status_code == 200:
    #         prefix = 'Data point %d sent' % i
    #     else:
    #         prefix = 'Error sending point %d' % i
    #     print('%s to Thingspeak: %d %s' % (prefix, res.status_code, res.text))
        
    #     del res

    # print('Data sent to Thingspeak')
    
    # from thingspeak import Channel

    # channel_weather_station = 'Weather Station Data'

    # channels = [
    #     Channel(channel_weather_station, api_key, [
    #         'Temperature',
    #         'Humidity',
    #         'Dewpoint',
    #         'Dewpoint Spread',
    #         'Heat Index',
    #         'Pressure',
    #         'Relative Pressure',
    #         'Voltage'
    #     ])
    # ]

    # from thingspeak import ThingSpeakAPI, ProtoHTTPS

    # print('Instantiating ThingSpeakAPI object')

    # thing_speak = ThingSpeakAPI(channels, protocol_class=ProtoHTTPS, log=True)

    # thing_speak.send(channel_weather_station, {
    #     'Temperature': result[0],
    #     'Humidity': result[1],
    #     'Dewpoint': result[2],
    #     'Dewpoint Spread': result[3],
    #     'Heat Index': result[4],
    #     'Pressure': result[5],
    #     'Relative Pressure': result[6],
    #     'Voltage': result[7]
    # })

    # print('Sent Thingspeak Data')
