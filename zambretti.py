def CalcuateTrend(language, pressure_value):
    import json, gc
    
    trend = 0
    trend_in_words = ''
    print('---> Calculating Pressure Trend')

    # weighted average calculation
    p_diff = (pressure_value[0] - pressure_value[1]) * 1.5
    for i, p_val in enumerate(pressure_value[2:], 2): # 12 elements currently, start i at 2
        p_diff += (pressure_value[0] - p_val) / (i * 0.5) # denominator: {1, 1.5, 2, ..., 5.5}
    p_diff = p_diff / 11

    print('Current trend:', p_diff)

    f = open('zamb_' + language + '.json', 'r')
    ZAMB = json.loads(f.read())

    if p_diff > 3.5:
        trend_in_words = ZAMB['TEXT_RISING_FAST']
        trend = 1
    elif p_diff > 1.5 and p_diff <= 3.5:
        trend_in_words = ZAMB['TEXT_RISING']
        trend = 1
    elif p_diff > 0.25 and p_diff <= 1.5:
        trend_in_words = ZAMB['TEXT_RISING_SLOW']
        trend = 1
    elif p_diff > -0.25 and p_diff <= 0.25:
        trend_in_words = ZAMB['TEXT_STEADY']
        trend = 0
    elif p_diff > -1.5 and p_diff <= -0.25:
        trend_in_words = ZAMB['TEXT_FALLING_SLOW']
        trend = -1
    elif p_diff > -3.5 and p_diff <= -1.5:
        trend_in_words = ZAMB['TEXT_FALLING']
        trend = -1
    elif p_diff <= -3.5:
        trend_in_words = ZAMB['TEXT_FALLING_FAST']
        trend = -1

    print('Current pressure trend: %s' % trend_in_words)

    del ZAMB
    gc.collect()

    return trend, trend_in_words

def ZambrettiLetter(rel_Pres_Rounded_hPa, z_trend, month):
    # Returns Zambretti Letter

    print('---> Calculating Zambretti letter')
    z_letter = ''
    # Case trend is falling
    if z_trend == -1:
        zambretti = (0.000974614 * rel_Pres_Rounded_hPa * rel_Pres_Rounded_hPa
                     - 2.10680 * rel_Pres_Rounded_hPa + 1138.70)
        if month < 4  or month > 9:
            zambretti = zambretti + 1
        int_zambretti = round(zambretti)
        print('Calculated and rounded Zambretti in numbers: ', end='')
        print(int_zambretti)
        if int_zambretti == 0:
            z_letter = 'A' #Settled Fine
        elif int_zambretti == 1:
            z_letter = 'A' #Settled Fine
        elif int_zambretti == 2:
            z_letter = 'B' #Fine Weather
        elif int_zambretti == 3:
            z_letter = 'D' #Fine Becoming Less Settled
        elif int_zambretti == 4:
            z_letter = 'H' #Fairly Fine Showers Later
        elif int_zambretti == 5:
            z_letter = 'O' #Showery Becoming unsettled
        elif int_zambretti == 6:
            z_letter = 'R' #Unsettled, Rain later
        elif int_zambretti == 7:
            z_letter = 'U' #Rain at times, worse later
        elif int_zambretti == 8:
            z_letter = 'V' #Rain at times, becoming very unsettled
        elif int_zambretti == 9:
            z_letter = 'X' #Very Unsettled, Rain

    # Case trend is steady
    if z_trend == 0:
        #zambretti = 138.24 - 0.133 * rel_Pres_Rounded_hPa
        zambretti = (-1.36338E-4 * rel_Pres_Rounded_hPa * rel_Pres_Rounded_hPa
                     + 0.138805 * rel_Pres_Rounded_hPa + 2.77547)
        int_zambretti = round(zambretti)
        print('Calculated and rounded Zambretti in numbers: ', end='')
        print(int_zambretti)
        if int_zambretti == 0:
            z_letter = 'A' #Settled Fine
        elif int_zambretti == 1:
            z_letter = 'A' #Settled Fine
        elif int_zambretti == 2:
            z_letter = 'B' #Fine Weather
        elif int_zambretti == 3:
            z_letter = 'E' #Fine, Possibly showers
        elif int_zambretti == 4:
            z_letter = 'K' #Fairly Fine, Showers likely
        elif int_zambretti == 5:
            z_letter = 'N' #Showery Bright Intervals
        elif int_zambretti == 6:
            z_letter = 'P' #Changeable some rain
        elif int_zambretti == 7:
            z_letter = 'S' #Unsettled, rain at times
        elif int_zambretti == 8:
            z_letter = 'W' #Rain at Frequent Intervals
        elif int_zambretti == 9:
            z_letter = 'X' #Very Unsettled, Rain
        elif int_zambretti >= 10:
            z_letter = 'Z' #Stormy, much rain

    # Case trend is rising
    if z_trend == 1:
        #zambretti = 160.346 - 0.155 * rel_Pres_Rounded_hPa
        zambretti = (-3.50216E-05 * rel_Pres_Rounded_hPa * rel_Pres_Rounded_hPa
                     - 0.0857548 * rel_Pres_Rounded_hPa + 126.111)
        #A Summer rising, improves the prospects by 1 unit over a Winter rising
        if month < 4 or month > 9:
            zambretti = zambretti + 1
        int_zambretti = round(zambretti)
        print('Calculated and rounded Zambretti in numbers: ', end='')
        print(int_zambretti)
        if int_zambretti == 0:
            z_letter = 'A' #Settled Fine
        elif int_zambretti == 1:
            z_letter = 'A' #Settled Fine
        elif int_zambretti == 2:
            z_letter = 'B' #Fine Weather
        elif int_zambretti == 3:
            z_letter = 'C' #Becoming Fine
        elif int_zambretti == 4:
            z_letter = 'F' #Fairly Fine, Improving
        elif int_zambretti == 5:
            z_letter = 'G' #Fairly Fine, Possibly showers, early
        elif int_zambretti == 6:
            z_letter = 'I' #Showery Early, Improving
        elif int_zambretti == 7:
            z_letter = 'J' #Changeable, Improving
        elif int_zambretti == 8:
            z_letter = 'L' #Rather Unsettled Clearing Later
        elif int_zambretti == 9:
            z_letter = 'M' #Unsettled, Probably Improving
        elif int_zambretti == 10:
            z_letter = 'Q' #Unsettled, short fine Intervals
        elif int_zambretti == 11:
            z_letter = 'T' #Very Unsettled, Finer at times
        elif int_zambretti == 12:
            z_letter = 'Y' #Stormy, possibly improving
        elif int_zambretti >= 13:
            z_letter = 'Z' #Stormy, much rain
    print('This is Zambretti\'s famous letter: %s' % z_letter)

    return z_letter

def ZambrettiSays(language, code):
    # Translates letter to Zambretti prediction

    import json, gc

    f = open('zamb_' + language + '.json', 'r')
    ZAMB = json.loads(f.read())
    
    if code:
        zambrettis_words = ZAMB['TEXT_ZAMBRETTI_' + code]
    else:
        zambrettis_words = ZAMB['TEXT_ZAMBRETTI_DEFAULT']

    del ZAMB
    gc.collect()

    return zambrettis_words

def MakePrediction(language, rel_Pres_Rounded_hPa, pressure_value, accuracy, month):
    accuracy_in_percent = int(accuracy * 94 / 12)

    trend, trend_in_words = CalcuateTrend(language, pressure_value)

    ZambrettisWords = ZambrettiSays(language, ZambrettiLetter(rel_Pres_Rounded_hPa, trend, month))
    print('**********************************************************')
    print('Zambretti says: %s, ' % ZambrettisWords, end='')
    print('Prediction accuracy: %d%%' % accuracy_in_percent)
    if accuracy < 12:
        print('Reason: Not enough data yet.')
        print('We need %d hours more to get sufficient data.' % ((12 - accuracy) / 2))
    print('**********************************************************')

    return ZambrettisWords, trend_in_words, accuracy_in_percent
