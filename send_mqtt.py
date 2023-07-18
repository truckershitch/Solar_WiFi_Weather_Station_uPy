from user_except import CustomNetworkError

def SendToMQTT(CONF, result):
    from umqtt.simple import MQTTClient

    paused = False
        
    def sub_cb(topic, msg):
        nonlocal paused
        if topic == CONF['mqttSubTopic'].encode():
            print('msg = "%s": ' % msg, end='')
            if msg == b'on':
                # don't sleep
                paused = True
                suffix = 'pause'
            else:
                suffix = 'continue'
            print('Weather station will %s' % suffix)

    def connect_and_subscribe():
        client = MQTTClient(CONF['mqttClientName'],
                            CONF['mqttBroker'],
                            CONF['mqttPort'],
                            CONF['mqttUser'],
                            CONF['mqttPass'],
                            keepalive=60)
        # Subscribed messages will be delivered to this callback
        client.set_callback(sub_cb)
        client.connect()
        client.subscribe(CONF['mqttSubTopic'].encode()) # where we see if motion is active
        print('Connected to %s, subscribed to %s topic' % (CONF['mqttBroker'],
                                                           CONF['mqttSubTopic']))

        return client

    def publish(client, topic, msg):
        try:
            client.publish(topic, msg, qos=1)
            return True
        except OSError:
            print('Failed to send payload to MQTT Broker')
            return False
    
    def create_payload():
        import json

        myPayload = json.dumps({'values': result})

        return myPayload

    send_payload = False
    prefix = ''
    try:
        client = connect_and_subscribe()
        send_payload = True
        prefix = 'Connected'
    except OSError:
        prefix = 'Failed to connect'
        raise CustomNetworkError('%s to MQTT Broker')

    print('%s to MQTT Broker' % prefix)

    wait_timeout = 0
    while wait_timeout < 3:
        client.check_msg()        
        wait_timeout += 0.1

    if send_payload:
        payload = create_payload()
        if publish(client, CONF['mqttPubTopic'].encode(), payload.encode()):
            prefix = 'Sucessfully sent'
        else:
            prefix = 'Failed to send'
        print('%s payload to MQTT Broker' % prefix)

    client.disconnect()

    return paused