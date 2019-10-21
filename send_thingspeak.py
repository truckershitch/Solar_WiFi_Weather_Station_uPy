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
    