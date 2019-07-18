def SendToBlynk(blynk_auth, result):
    # from time import sleep
    # import urequests

    # blynk_host = 'https://blynk-cloud.com'

    # for i, value in enumerate(result):
    #     res = urequests.put(url='%s/%s/update/V%d' % (blynk_host, blynk_auth, i), json=['%s' % value])
    #     if res.status_code != 200:
    #         print('Error updating pin V%d: %d %s' % (i, res.status_code, res.text))
    #     else:
    #         print('Updated pin V%d' % i)
    #     del res
    #     sleep(0.25)

    # print('Data written to Blynk')

    from time import sleep
    import sys, gc
    import blynklib

    blynk = blynklib.Blynk(blynk_auth, server='192.168.1.48', port=8080)

    CONNECT_PRINT_MSG = '[CONNECT_EVENT]'
    DISCONNECT_PRINT_MSG = '[DISCONNECT_EVENT]'

    @blynk.handle_event("connect")
    def connect_handler():
        print(CONNECT_PRINT_MSG)
        print('Sleeping 1 sec in connect handler...')
        sleep(1)
        for i, value in enumerate(result):
            print('Writing pin V%d' % i)
            blynk.virtual_write(i, value)
        blynk.disconnect()

    @blynk.handle_event("disconnect")
    def connect_handler():
        print(DISCONNECT_PRINT_MSG)
        print('Sleeping 1 sec in disconnect handler...')
        sleep(1)

    blynk.run()

    del blynk
    del sys.modules['blynklib']
    gc.collect()
