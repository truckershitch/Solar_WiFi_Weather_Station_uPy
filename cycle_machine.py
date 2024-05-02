def WriteError(errorfile, reason, timestamp):
    f = open(errorfile, 'a+')
    f.write('%s' % reason)
    if timestamp:
        from weather_station import FmtDateTime
        f.write(' at %s' % FmtDateTime(timestamp))
    f.write('\n')
    f.close()

def GoToSleep8266(sleep_time_secs):
    # sleep_time_secs may be a float
    import machine
    from time import localtime, sleep
    # from user_except import CustomResetError

    if sleep_time_secs <= 0:
        print('Tried to sleep for %s seconds. Calling reset')
        machine.reset()

    sleep(1)

    calib = 41 * sleep_time_secs # rtc is a little fast!
    nap_time_ms = sleep_time_secs * 1000 + calib

    print('Going to sleep now for roughly %d minute(s).'
        % localtime(round(nap_time_ms / 1000))[4])

    rtc = machine.RTC()
    # configure rtc.ALARM0 to wake up device
    rtc.irq(trigger=rtc.ALARM0, wake=machine.DEEPSLEEP)
    # set the timer (milliseconds)
    rtc.alarm(rtc.ALARM0, round(nap_time_ms))
    # take a nap
    machine.deepsleep()

def GoToSleep(sleep_time_secs):
    import machine
    from time import localtime

    if sleep_time_secs <= 0:
        print('Tried to sleep for %s seconds. Calling reset')
        machine.reset()
    
    calib = 41 * sleep_time_secs # rtc is a little fast!
    nap_time_ms = sleep_time_secs * 1000 + calib
    
    print('Going to sleep now for roughly %d minute(s).'
        % localtime(round(nap_time_ms / 1000))[4])

    machine.deepsleep(round(nap_time_ms))