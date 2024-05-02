# sunrise / sunset calculation
# https://gml.noaa.gov/gdeg_to_rad/solcalc/solareqns.PDF

from math import sin, cos, acos, tan
import time

def calculations(ts, latitude):
    def deg_to_rad(deg):
        return deg * 3.1416 / 180

    def rad_to_deg(rad):
        return rad * 180 / 3.1416

    # day of year
    doy = time.gmtime(ts)[7]

    # fractional year
    # fy = 2 * 3.1416 / 365 * (doy - 1 + ((hour - 12) / 24))
    fy = 2 * 3.1416 / 365 * (doy - 0.5)

    # equation of time
    eqtime = 229.18 * (
        0.000075 + 0.001868 * cos(fy)
        - 0.032077 * sin(fy) - 0.014615 * cos(2 * fy)
        - 0.040849 * sin(2 * fy)
    )

    # solar declination angle
    decl = (
        0.006918 - 0.399912 * cos(fy)
        + 0.070257 * sin(fy) - 0.006758 * cos(2 * fy)
        + 0.000907 * sin(2 * fy) - 0.002697 * cos(3 * fy)
        + 0.00148 * sin (3 * fy)
    )

    # hour angle
    ha = rad_to_deg(acos(cos(deg_to_rad(90.833)) / cos(deg_to_rad(latitude)) / cos(decl) - tan(deg_to_rad(latitude)) * tan(decl)))

    return ha, eqtime

# utc_offset in minutes, dst_offset in seconds
def sunrise(latitude, longitude, ts, utc_offset, dst_offset):
    (ha, eqtime) = calculations(ts, latitude)
    utc_sunrise = 720 - 4 * (longitude + ha) - eqtime
    sunrise_secs = int(utc_sunrise + utc_offset * 60) * 60 + dst_offset
    return midnight_time(ts, sunrise_secs)

def sunset(latitude, longitude, ts, utc_offset, dst_offset):
    (ha, eqtime) = calculations(ts, latitude)
    utc_sunset = 720 - 4 * (longitude - ha) - eqtime
    sunset_secs = int(utc_sunset + utc_offset * 60) * 60 + dst_offset
    return midnight_time(ts, sunset_secs)

def solar_noon(latitude, longitude, ts, utc_offset, dst_offset):
    (ha, eqtime) = calculations(ts, latitude)
    utc_solar_noon = 720 - 4 * longitude - eqtime
    solar_noon_secs = int(utc_solar_noon + utc_offset * 60) * 60 + dst_offset
    return midnight_time(ts, solar_noon_secs)

def midnight_time(ts, diff):
    mins, secs = divmod(diff, 60)
    hrs, mins = divmod(mins, 60)

    t_tup = time.localtime(ts)
    mn_time = time.mktime((
        t_tup[0],
        t_tup[1],
        t_tup[2],
        hrs,
        mins,
        secs,
        t_tup[6],
        t_tup
    ))
    return mn_time