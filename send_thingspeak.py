def SendToThingspeak(host, user, api_key, channel_id, result):
    from umqtt.simple import MQTTClient

    try:
        client = MQTTClient(
            client_id='umqtt_client',
            server=host,
            user=user,
            password=api_key,
            ssl=False)

        topic = 'channels/%s/publish/%s' % (channel_id, api_key)

        payload = (''.join(['&field%d=%.2f' % (x + 1, result[x]) for x in range(8)]) +
                '&status=Pressure: %s; Forecast: %s; Accuracy: %s percent'
                % (result[10], result[9], result[8]))[1:]
                
        client.connect()
        client.publish(topic, payload)
        client.disconnect()

        print('Sent data to Thingspeak via MQTT')
    except:
        print('Failed to send data to Thingspeak via MQTT')
