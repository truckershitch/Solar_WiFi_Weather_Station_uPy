def SummerTimeAdjustment(country, current_timestamp):
    # See if Summer Time is active -- if so, adjust time and flag
    # With a proper country.json file, this should work for many countries

    import time, json

    def load_time_data(time_data):
        season_data = time_data['winter_time']
        properties = season_data.keys()
        for prop in properties:
            WIN[season_data[prop]['short']] = season_data[prop]['value']

        season_data = time_data['summer_time']
        properties = season_data.keys()
        for prop in properties:
            SUM[season_data[prop]['short']] = season_data[prop]['value']

    def CheckBorderMonths():
        # We are in a month of a time change

        def GetTargetTimestamp(time_data):
            # Inspired by pourhaus's comment here: https://bit.ly/2Wei1vO
            # time_data['last'] == last day of month that the target
            # weekday could occur, e.g. First Sunday, time_data['last'] = 7;
            # Second Saturday: 14; Last weekday: -1
            # first_day == first day of that seven day period

            last_dom = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
            year = time.localtime(current_timestamp)[0]

            first_day = time_data['last'] - 6
            if time_data['last'] == -1: # last weekday of month
                if time_data['mon'] == 2 and year % 4 == 0:
                     # there is more to leap year but why bother? I'll be dead
                    first_day = 29 - 6 # leap year
                else:
                    first_day = last_dom[time_data['mon'] - 1] - 6

            target = time.mktime((  year,
                                    time_data['mon'],
                                    first_day,
                                    time_data['hr'],
                                    time_data['min'],
                                    0,
                                    None, None  ))
            weekday = time.localtime(target)[6]
            if weekday != time_data['wd']:
                target += ((time_data['wd'] - weekday) % 7) * SECS_IN_DAY
            
            return target

        if mon == SUM['mon']: # Summer Time month
            if current_timestamp >= GetTargetTimestamp(SUM):
                return True
            else:
                return False

        else:  # Daylight Saving Time month
            if curr_dst_status >= GetTargetTimestamp(WIN):
                return False
            else:
                return True
    
    WIN, SUM = {}, {}
    SECS_IN_DAY = 86400

    curr_dst_status = 0
    adjust = False

    ts_local = time.localtime(current_timestamp)
    mon = ts_local[1] # month

    f = open('dst_' + country + '.json', 'r')
    time_data = json.loads(f.read())
    load_time_data(time_data)
    DST_ADJ_AMT = time_data['minutes_to_adjust'] * 60

    if SUM['mon'] < WIN['mon']: # Northern Hemisphere probably
        if   mon > SUM['mon'] and mon < WIN['mon']: # Summer Time
            adjust = True
        elif mon < SUM['mon'] or  mon > WIN['mon']: # DST
            adjust = False
        else:
            adjust = CheckBorderMonths()

    else: # upside down!
        if   mon > WIN['mon'] and mon < SUM['mon']: # DST
            adjust = False
        elif mon < WIN['mon'] or  mon > SUM['mon']: # Summer Time
            adjust = True
        else:
            adjust = CheckBorderMonths()

    if adjust:
        curr_dst_status = 1
        current_timestamp += DST_ADJ_AMT

    return curr_dst_status, current_timestamp, DST_ADJ_AMT