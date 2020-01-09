def SendToThingspeak(host, api_key, channel_id, result):
    from umqtt.simple import MQTTClient

    try:
        client = MQTTClient('umqtt_client', host)

        topic = 'channels/%s/publish/%s' % (channel_id, api_key)

        payload = (''.join(['&field%d=%.2f' % (x + 1, result[x]) for x in range(8)]) +
                '&status=Pressure: %s; Forecast: %s; Accuracy: %s percent'
                % (result[10], result[9], result[8]))[1:]
                
        client.connect()
        client.publish(topic, payload)
        client.disconnect()

        print('Payload: %s' % payload)
        print('Sent data to Thingspeak via MQTT')
    except:
        print('Failed to send data to Thingspeak via MQTT')
