def ResetMachine(ERRORFILE=None, reason=None):
    from time import sleep
    import machine

    if ERRORFILE and reason:
        f = open(ERRORFILE, 'a+')
        f.write('%s\n' % reason)
        f.close()

    machine.reset()
    sleep(5) # reset is not immediate

def GoToSleep(sleep_time_secs, ERRORFILE=None, reason=None):
    from time import localtime
    import machine

    if ERRORFILE and reason:
        f = open(ERRORFILE, 'a+')
        f.write('%s\n' % reason)
        f.close()

    calib = 41 * sleep_time_secs # rtc is a little fast!
    nap_time_ms = sleep_time_secs * 1000 + calib

    print('Going to sleep now for roughly %d minute(s).'
        % localtime(int(nap_time_ms / 1000))[4])

    rtc = machine.RTC()
    # configure rtc.ALARM0 to wake up device
    rtc.irq(trigger=rtc.ALARM0, wake=machine.DEEPSLEEP)
    # set the timer (milliseconds)
    rtc.alarm(rtc.ALARM0, int(nap_time_ms))
    # take a nap
    machine.deepsleep()
