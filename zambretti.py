def CalculateTrend(language, pressure_value):
    # See https://www.statisticshowto.com/sens-slope-theil-sen-estimator/
    import json, gc
    
    print('---> Calculating Pressure Trend using Sens Slope')

    # calculate all slopes
    slopes = []
    n = len(pressure_value)
    
    for i in range(n):
        for j in range(i + 1, n):
            slopes.append((pressure_value[i] - pressure_value[j]) / (j - i))

    slope_count = len(slopes)
    slopes.sort()

    # calculate median of slopes
    if slope_count % 2 == 0:
        median_1 = slopes[slope_count // 2]
        median_2 = slopes[slope_count // 2 - 1]
        median = (median_1 + median_2) / 2
    else:
        median = slopes[slope_count // 2]

    print('Current trend: %.02f' % median)

    f = open('zamb_%s.json' % language, 'r')
    ZAMB = json.loads(f.read())

    # values subject to change
    if     1    <= median:
        trend_in_words = ZAMB['TEXT_RISING_FAST']
        trend = 1
    elif   0.60 <= median <   1:
        trend_in_words = ZAMB['TEXT_RISING']
        trend = 1
    elif   0.27 <= median <   0.6:
        trend_in_words = ZAMB['TEXT_RISING_SLOW']
        trend = 1
    elif  -0.27 <  median <   0.27:
        trend_in_words = ZAMB['TEXT_STEADY']
        trend = 0
    elif  -0.60 <  median <= -0.27:
        trend_in_words = ZAMB['TEXT_FALLING_SLOW']
        trend = -1
    elif  -1    <  median <= -0.6:
        trend_in_words = ZAMB['TEXT_FALLING']
        trend = -1
    elif           median <= -1:
        trend_in_words = ZAMB['TEXT_FALLING_FAST']
        trend = -1

    print('Current pressure trend: %s' % trend_in_words)

    del ZAMB
    gc.collect()

    return trend, trend_in_words

# def ZambrettiLetter(rel_Pres_Rounded_hPa, z_data, z_trend, month):
## TODO
def ZambrettiLetter(rel_Pres_Rounded_hPa, z_data, z_trend, month):
    # Calculates and returns Zambretti Letter

    def limit(num, minimum, maximum):
        # keep num in range of maximum and minimum
        return max(min(num, maximum), minimum)

    def is_summer():
        if hemisphere == 'N':
            if 5 < month < 10:
                return True
        elif hemisphere == 'S':
            if month < 3 or month > 10:
                return True
        return False

    def is_winter():
        if hemisphere == 'N':
            if month < 3 or month > 10:
                return True
        elif hemisphere == 'S':
            if 5 < month < 10:
                return True
        return False

    print('---> Calculating Zambretti letter')

    letters =   {
                   -1: ['A', 'B', 'D', 'H', 'O', 'R',
                        'U', 'V', 'X'],
                    0: ['A', 'B', 'E', 'K', 'N', 'P',
                        'S', 'W', 'X', 'Z'],
                    1: ['A', 'B', 'C', 'F', 'G', 'I',
                        'J', 'L', 'M', 'Q', 'T', 'Y', 'Z']
                }
    constants = {
                    -1: {'a':  0.000974614, 'b': -2.10680,   'c': 1138.70   },
                     0: {'a': -1.36338E-4,  'b':  0.138805,  'c':    2.77547},
                     1: {'a':  1.01291E-4,  'b': -0.352833,  'c':  256.876  }
                }
    # range of pressure in Zambretti chart
    PZ_MIN, PZ_MAX = 947, 1050
    # local area pressure range
    Pl_Min, Pl_Max = z_data['PRESSURE']['PRESSURE_MIN'], z_data['PRESSURE']['PRESSURE_MAX']
    hemisphere = z_data['HEMISPHERE'] # 'N' or 'S' (or neither)

    # linearly adjust pressure to range of pressures in Zambretti chart
    Pz = ( ( rel_Pres_Rounded_hPa * (PZ_MAX - PZ_MIN)
             - PZ_MAX * Pl_Min
             + PZ_MIN * Pl_Max ) / 
           (Pl_Max - Pl_Min) )

    # use quadratic regression to get Zambretti value
    # ax^2 + bx + c
    a, b, c = (constants[z_trend]['a'],
               constants[z_trend]['b'],
               constants[z_trend]['c'])
    zambretti = round(a * Pz * Pz + b * Pz + c)

    # crude adjustment for winter/summer
    if z_trend == -1:
        if is_winter():
            zambretti -= 1
    elif z_trend == 1:
        if is_summer():
            zambretti += 1

    zambretti = limit(zambretti, 1, len(letters[z_trend]))
    z_letter = letters[z_trend][zambretti - 1] # list starts at 0
    
    print('Calculated and rounded Zambretti value: %d' % zambretti)
    print('This is Zambretti\'s famous letter: %s' % z_letter)

    return z_letter

def ZambrettiSays(language, code):
    # Translates letter to Zambretti prediction

    import json, gc

    f = open('zamb_' + language + '.json', 'r')
    ZAMB = json.loads(f.read())
    f.close()
    
    if code:
        zambrettis_words = ZAMB['TEXT_ZAMBRETTI_%s' % code]
    else:
        zambrettis_words = ZAMB['TEXT_ZAMBRETTI_DEFAULT']

    del ZAMB
    gc.collect()

    return zambrettis_words

# def MakePrediction(language, z_data, rel_Pres_Rounded_hPa, pressure_value, accuracy, month):
## TODO
def MakePrediction(z_data, rel_Pres_Rounded_hPa, pressure_value, accuracy, month):
    pval_count = len(pressure_value)
    accuracy_in_percent = int(accuracy * 94 / pval_count)

    # trend, trend_in_words = CalculateTrend(language, pressure_value)
    ## TODO
    trend, trend_in_words = CalculateTrend(z_data['LANGUAGE'], pressure_value)

    # ZambrettisWords = ZambrettiSays(language, ZambrettiLetter(rel_Pres_Rounded_hPa, z_data, trend, month))
    ## TODO
    ZambrettisWords = ZambrettiSays(z_data['LANGUAGE'], ZambrettiLetter(rel_Pres_Rounded_hPa, z_data, trend, month))
    print('**********************************************************')
    print('Zambretti says: %s, ' % ZambrettisWords, end='')
    print('Prediction accuracy: %d%%' % accuracy_in_percent)
    if accuracy < pval_count:
        print('Reason: Not enough data yet.')
        print('We need %s hours more to get sufficient data.' % ((pval_count - accuracy) / 2))
    print('**********************************************************')

    return ZambrettisWords, trend_in_words, accuracy_in_percent
