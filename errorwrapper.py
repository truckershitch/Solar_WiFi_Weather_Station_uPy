# Logs error from passed-in function to a file
#
# Usage:
# wrapper = ErrorWrapper(logfile)
# def f(a, b, c)
# wrapper.wrap(f, a, b, c=3)
#
# Last update June 23, 2023
# 2023-05-29 -- added set_ts()
# 2023-06-23 -- added custom errors, write_exception()

from user_except import CustomNetworkError, CustomResetError, CustomHWError, CustomMoistureSensorError

class ErrorWrapper(object):
    def __init__(self, log, timestamp=None, sleep_mins=10):
        self._log = log
        self._timestamp = timestamp
        self._sleep_mins = sleep_mins

    def set_ts(self, timestamp):
        self._timestamp = timestamp

    def write_exception(self, exception):
         import sys

         with open(self._log, 'a') as file:
            if self._timestamp is not None:
                from weather_station import FmtDateTime
                file.write('%s\n' % FmtDateTime(self._timestamp))
            sys.print_exception(exception, file)
         print('Error: Logged to %s' % self._log)

    def sleep_it_off(self, exc, mins=None, log=True):
        from cycle_machine import GoToSleep
        sleep_mins = mins if mins is not None else self._sleep_mins

        if log:
            self.write_exception(exception=exc)
        print('Sleeping for %d minutes' % sleep_mins)
        GoToSleep(sleep_time_secs=sleep_mins * 60)

    def call_reset(self, exc):
        import machine

        self.write_exception(exception=exc)
        print('Calling machine.reset()')
        machine.reset()

    def wrap(self, fn, *args, **kwargs):
        # consider adding function and args/kargs to log file
        try:
            output = fn(*args, **kwargs)
            if output != None:
                return output

        except CustomNetworkError as cne:
            self.sleep_it_off(exc=cne)

        except CustomResetError as cre:
            self.call_reset(exc=cre)

        except CustomHWError as chwe:
            self.sleep_it_off(exc=chwe, mins=3)

        except CustomMoistureSensorError as cmse:
            self.sleep_it_off(exc="Error reading moisture sensor", mins=3)

        except Exception as e:
            self.call_reset(exc=e)
