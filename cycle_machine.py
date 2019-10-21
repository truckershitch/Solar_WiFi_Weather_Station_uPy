def WriteError(errorfile, reason, timestamp):
    f = open(errorfile, 'a+')
    f.write('%s' % reason)
    if timestamp:
        from weather_station import FmtDateTime
        f.write(' at %s' % FmtDateTime(timestamp))
    f.write('\n')
    f.close()

def ResetMachine(errorfile=None, reason=None, timestamp=None):
    from time import sleep
    import machine

    if errorfile and reason:
        WriteError(errorfile, reason, timestamp)

    machine.reset()
    sleep(5) # reset is not immediate

def GoToSleep(sleep_time_secs, errorfile=None, reason=None, timestamp=None):
    # sleep_time_secs may be a float
    
    from time import localtime
    import machine

    if sleep_time_secs <= 0:
        ResetMachine(errorfile,
                    'Tried to sleep for %s seconds'
                    % sleep_time_secs, timestamp)

    if errorfile and reason:
        WriteError(errorfile, reason, timestamp)

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
