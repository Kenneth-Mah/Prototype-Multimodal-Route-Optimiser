from MSCFunction import *

#MSCFunction takes the following input parameters:
#(mode, start_port, end_port, dep_date, opti, connection_time, remove_port, remove_trip, constraints)
# remove and constraint parameters are default arguments, can be excluded.

#It returns the following output parameters:
# [route1, parameters1], [route2, parameters2], [route3, parameters3].
# Please consult the Agenda document for a full description of route and parameter format.

# Due to randomness in the generator function for cost and carbon emissions, their output parameters may vary.
# Setting too strict a constraint may result in some runs having no routes, other runs having one, or two routes generated.

def task1():
    # Find a multimodal route from New Zealand to UK that minimises the transit time,
    # given a departure date of 31st July 2022, connection time of 12 hours,
    # And a time constraint of 36 days.
    print("Task 1")
    receive = MSCModel('M', 'NZAKL', 'LHR', '20220731', '0', '12',[], [],[36,0,0])
    for result in receive:
        print(result)
        print('\n')
    return

task1()
        


def task2():
    #Find the same route as task1, but exclude the last trip from your answer in (a), exclude the port SGSIN,
    # and replace the carbon constraint with a cost constraint of $6250.
    print("Task 2")
    exclude = MSCModel('M', 'NZAKL', 'LHR', '20220731', '0', '12',['SGSIN'],[('SIN','SQ7396', '20220902', '0145')], [0,6250,0])
    for result in exclude:
        print(result)
        print('\n')

task2()

#ERROR HANDLING:

#ERROR 1: Start / end port doesn't exist

def error1():
    lol = MSCModel('M', 'YOUR', 'MOM', '20220731', '0', '12',['SGSIN'],[('SIN','SQ7396', '20220902', '0145')], [0,6250,0])

#error1()

#ERROR 2: Date is not in proper format. Note that "proper" just means an 8-digit numeric string. Ideally it should be YYYYMMDD. 

def error2():
    lol = MSCModel('M', 'CNQZH', 'INNSA', '31st July 2022', '0', '12',['SGSIN'],[('SIN','SQ7396', '20220902', '0145')], [0,6250,0])
    return

# error2()

#ERROR 3: Wrong optimiser. Only 3 numbers - 0 for time, 1 for cost, 2 for carbon. Naming the optimiser is not allowed.

def error3():
    lol = MSCModel('M', 'CNQZH', 'INNSA', '20220731', 'time', '12',['SGSIN'],[('SIN','SQ7396', '20220902', '0145')], [0,6250,0])


#error3()

#ERROR 4: Invalid connection_time. 0 is technically valid, but makes no sense.

def error4():
    lol = MSCModel('M', 'CNQZH', 'INNSA', '20220731', '0', 'NO',['SGSIN'],[('SIN','SQ7396', '20220902', '0145')], [0,6250,0])

#error4()

#ERROR 5: Ports to remove don't exist / are invalid / have been removed

def error5():
    lol = MSCModel('M', 'CNQZH', 'INNSA', '20220731', '0', '12',['BURN IT DOWN'],[('SIN','SQ7396', '20220902', '0145')], [0,6250,0])
    
#error5()

#ERROR 6: Trips to remove contain a port that falls under ERROR 5, or have an invalid date-time.
# If a trip is already removed, no error raised.

def error6():
    lol = MSCModel('M', 'CNQZH', 'INNSA', '20220731', '0', '12',['SGSIN'],[('SIN','WRONG FLIGHT', '20220902', '0145')], [0,6250,0])

error6()
#ERROR 7: Constraints are given in improper format.
