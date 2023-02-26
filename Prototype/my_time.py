#time-correcting function
def time_correct(time_check, start, end):
    year_check = int(str(end)[:4]) - int(str(start)[:4])

    if year_check > 0:
        #the year has changed.
        prev_year = str(start)[:4] + '1231235900'
        next_year = str(end)[:4] + '0101000000'
        time_check =  time_correct((end - int(next_year))/1000000, next_year, end) + time_correct((int(prev_year) - start)/ 1000000, start,prev_year)

        fix = (time_check - int(time_check)) * 10000
        while fix >= 2400:
            time_check += 1
            time_check -= 0.24
            fix -= 2400

        last = str(int(fix))[-2:]
        if int(last) > 60:
            time_check += 0.01
            time_check -= 0.006

        if (time_check - int(time_check)) * 10000 > 2400:
            time_check += 1
            time_check -= 0.24

        return time_check
        

    month = int(str(start)[4:6])
    count = int(str(end)[4:6]) - month 
    while count >= 1:
        #the month has changed. Odd months before August have 31 days. Even months from August have 30 days.
        if month == 2:
            #Assume Feb has 28 days.
            time_check -= 72
        elif (month % 12 < 8 and month % 2 == 1) or (month % 12 >= 8 and month % 2 == 0):
            time_check -= 69
        else:
            time_check -= 70
        month += 1
        count -= 1

##    fix = (time_check - int(time_check)) * 10000
##    while fix >= 2400:
##        time_check += 1
##        time_check -= 0.24
##        fix -= 2400
##
##    last = str(int(fix))[-2:]
##    if int(last) > 60:
##        time_check += 0.01
##        time_check -= 0.006
##
##    if (time_check - int(time_check)) * 10000 > 2400:
##        time_check += 1
##        time_check -= 0.24

    return time_check
        
