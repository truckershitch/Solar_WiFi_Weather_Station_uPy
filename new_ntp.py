import utime

try:
    import usocket as socket
except:
    import socket
try:
    import ustruct as struct
except:
    import struct

# The NTP host can be configured at runtime by doing: ntptime.host = 'myhost.org'
# host = "pool.ntp.org"
# host = '192.168.1.50'
# The NTP socket timeout can be configured at runtime by doing: ntptime.timeout = 2
timeout = 2


def time(host):
    NTP_QUERY = bytearray(48)
    NTP_QUERY[0] = 0x1B
    addr = socket.getaddrinfo(host, 123)[0][-1]
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.settimeout(timeout)
        res = s.sendto(NTP_QUERY, addr)
        msg = s.recv(48)
    except OSError: # timeout
        return 0
    finally:
        s.close()
    val = struct.unpack("!I", msg[40:44])[0]

    EPOCH_YEAR = utime.gmtime(0)[0]
    if EPOCH_YEAR == 2000:
        # (date(2000, 1, 1) - date(1900, 1, 1)).days * 24*60*60
        NTP_DELTA = 3155673600
    elif EPOCH_YEAR == 1970:
        # (date(1970, 1, 1) - date(1900, 1, 1)).days * 24*60*60
        NTP_DELTA = 2208988800
    else:
        print("Unsupported epoch: {}".format(EPOCH_YEAR))
        return 0

    return val - NTP_DELTA

def asctime():  # get human readable version
    x=utime.localtime()
    return '%02d/%02d/%04d %02d:%02d' % (x[1],x[2],x[0],x[3],x[4])
    # like 12/13/2017 14:31

# There's currently no timezone support in MicroPython, and the RTC is set in UTC time.
def settime(host):
    t = time(host)
    import machine

    try:
        tm = utime.gmtime(t)
    except OverflowError:
        return False
    machine.RTC().datetime((tm[0], tm[1], tm[2], tm[6] + 1, tm[3], tm[4], tm[5], 0))
    if t != 0:
        print("Time sync: %s UTC" % asctime())
        return True
    else:
        return False
