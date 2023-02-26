import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from random import randint
from DijkstraFunction import Node, Edge, Dijkstra #shortest path algo
from my_time import time_correct


##THROWING THE WHOLE THING INTO A FUNCTION

def MSCModel(mode, start_port, end_port, dep_date, opti, connection_time, exclude_ports = None, exclude_trips = None, constraints = [0,0,0]):
    #mode, start_port, end_port - character strings
    #dep_date - YYYYMMDD
    #opti - 0 (time), 1 (cost), 2 (carbon)
    #connection_time - in hours

    #remove_ports - list of ports  to remove. If no ports to remove, default to None.
    #remove_trips - list of trips to remove. Trips stored as tuples. If no trips to remove, default to None.
    #constraints - list of constraint values. Index corresponds to opti. [0,0,0] if None.

    ###----------------------------------PART I: Preparing the DataSets and Dictionaries
    #Datasets loaded here with pandas
    #CHANGE FILE LOCATION TO WHERE IT'S STORED IN YOUR COMPUTER.
    ocean_data = pd.read_excel(r"C:\Users\kenne\Desktop\Prototype\data\GlobalOceanSchedulesEdit.xlsx")
    air_data = pd.ExcelFile(r"C:\Users\kenne\Desktop\Prototype\data\GlobalAirSchedules2.xlsx")
    coord = pd.ExcelFile(r"C:\Users\kenne\Desktop\Prototype\data\Coordinates.xlsx")

    ##Changes made to the Coordinates File will be reflected here.
    sea_points = coord.parse('Seaport').values.tolist()
    air_points = coord.parse('Airport').values.tolist()
    port_pairs = coord.parse('Codex').values.tolist()
    flight_pairs = coord.parse('Flight Times').values.tolist()

    sea_coord = {} #Lat Long coordinates for sea ports.
    air_coord = {} #air ports.
    codex = {} #dictionary for matching up a country's sea and air port.
    flight_times_sg  = {} # Time needed to travel to another airport from Singapore's airport. 

    def create_coord(points,dic):
        for lst in points:
            name, country, lat, long = lst
            dic[name] = (lat,long)
        return dic

    def create_codex(pairs, dic):
        for lst in pairs:
            sea, air = lst
            dic[sea] = air
        return dic

    def create_flight_times(pairs, dic):
        for lst in pairs:
            air, time = lst
            dic[air] = time
        return dic

    create_coord(sea_points,sea_coord)
    create_coord(air_points, air_coord)
    create_codex(port_pairs, codex)
    create_flight_times(flight_pairs, flight_times_sg)
    ###-------------------------------------------------------SEAPORT DATASET
    # India (INNSA), China (CNQZH), Australia (AUMEL), New Zealand (NZAKL) and Singapore (SGSIN)
    # More ports can be easily added with larger datasets.

    ocean_df = pd.DataFrame(data = ocean_data)


    def datetoint(x):
        #Convert datetimes into integers. It was easier to work with.
        return int(x.strftime("%Y%m%d%H%M%S"))
    def inttodate(x):
        return datetime.strptime(str(x), "%Y%m%d%H%M%S")

    def transit(start, end): #takes pandas dataseries as input
        #calculates the duration of a trip in days-HHMM formaat. time_correct function handles discrepancies that arise when comparing dates.
        #We assume that a route won't take longer than 2 years (time won't be calculated correctly otherwise).
        lst_s = start.tolist()
        lst_e = end.tolist()

        times = []
        for i in range(0, len(lst_s)):
            time = lst_e[i] - lst_s[i]
            time = time_correct(time / 1000000, lst_s[i], lst_e[i])
            times.append(time)
        return pd.Series(times)

    ocean_df['Departs'] = ocean_df['Departs'].apply(datetoint)
    ocean_df['Arrives'] = ocean_df['Arrives'].apply(datetoint)
    ocean_df['Transit'] = transit(ocean_df['Departs'], ocean_df['Arrives'])



    ## If cost and carbon data provided directly, no need to initalise.

    #cost and carbon emissions calculated for 500 kg of cargo, shipped 4000 km.
    def cost(x, mode, weight = 500):
        #ocean transit $2-4 per kg,
        #air transit $4-8 per kg.
        
        if mode == 'SEA':
            cost = randint(200,400) / 100
        if mode == 'AIR':
            cost = randint(400,800) / 100
        x = weight * cost
        return x


    def carbon(x, mode, weight = 500, km = 4000):
        #CO2 emissions for sea - 10-40g per cargo metric ton (1000 kg) per km
        #CO2 emissions for air - 47x more.

        carbon = randint(10,40) 
        if mode == 'AIR':
            carbon *= 47
        x = weight * carbon * km / 1000
        return x / 1000

    ocean_df['Cost'] = ''
    ocean_df['Cost'] = ocean_df['Cost'].apply(lambda row: cost(row, 'SEA'))
    ocean_df['Carbon'] = ''
    ocean_df['Carbon'] = ocean_df['Carbon'].apply(lambda row: carbon(row, 'SEA'))



    ###------------------------------------------------------AIRPORT DATASET
    freight_out = air_data.parse('FOutbound')
    freight_in = air_data.parse('FInbound')
    pass_out = air_data.parse('POutbound')
    pass_in = air_data.parse('PInbound')


    # 4 SHEETS - Pax Inbound/ Outbound, Freight Inbound/Outbound


    def string(row):
        #had to rename the rows for flight_no.
        return str(row['Fltno'])

    def calc_lt_date(dic, name, time, mode):
        #apply time_delta to get arrival dates from departure data,
        # and departure dates from arrival data,
        # based on estimated time of travel as recorded in flight_times_sg.
        lst_T = time.apply(inttodate).tolist()
        lst_N = name.tolist()
        if mode == 'ARR':
            for i in range(0, len(lst_T)):
                lst_T[i] += timedelta(days = dic[name[i]] / 24)

            return pd.Series(lst_T).apply(datetoint)

        if mode == 'DEP':
            for i in range(0, len(lst_T)):
                lst_T[i] -= timedelta(days = dic[name[i]] / 24)

            return pd.Series(lst_T).apply(datetoint)

    #had to rename rows for LT DATEs as well. They weren't consistent across all sheets.

    #freight_out, freight_in - exact arr/dep times found using FlightAware

    freight_out['Air_Code'] = freight_out['Airline'] + freight_out.apply(lambda row: string(row), axis = 1)
    freight_out['LT Date (DEP)'] = freight_out['LT Date (DEP)'].apply(datetoint) + freight_out['DTime'] * 100
    freight_out['LT Date (ARR)'] = freight_out['LT Date (ARR)'].apply(datetoint) + freight_out['ATime'] * 100

    freight_in['Air_Code'] = freight_in['Airline'] + freight_in.apply(lambda row: string(row), axis = 1)
    freight_in['LT Date (DEP)'] = freight_in['LT Date (DEP)'].apply(datetoint) + freight_in['DTime'] * 100
    freight_in['LT Date (ARR)'] = freight_in['LT Date (ARR)'].apply(datetoint) + freight_in['ATime'] * 100

    freight_out['Transit'] = transit(freight_out['LT Date (DEP)'],freight_out['LT Date (ARR)'])
    freight_in['Transit'] = transit(freight_in['LT Date (DEP)'],freight_in['LT Date (ARR)'])

    freight_out['Cost'] = ''
    freight_out['Cost'] = freight_out['Cost'].apply(lambda row: cost(row, 'AIR'))
    freight_out['Carbon'] = ''
    freight_out['Carbon'] = freight_out['Carbon'].apply(lambda row: carbon(row, 'AIR'))

    freight_in['Cost'] = ''
    freight_in['Cost'] = freight_in['Cost'].apply(lambda row: cost(row, 'AIR'))
    freight_in['Carbon'] = ''
    freight_in['Carbon'] = freight_out['Carbon'].apply(lambda row: carbon(row, 'AIR'))

    #pass_out, pass_in - times of arr/dep calculated using flight_times_sg dictionary
    pass_out['Air_Code'] = pass_out['Airline'] + pass_out.apply(lambda row: string(row), axis = 1)
    pass_out['LT Date (DEP)'] = pass_out['LT Date (DEP)'].apply(datetoint) + pass_out['DTime'] * 100
    pass_out['LT Date (ARR)'] = calc_lt_date(flight_times_sg, pass_out['Dest & Coord. Orig/Dest Stn'], pass_out['LT Date (DEP)'], 'ARR')

    pass_in['Air_Code'] = pass_in['Airline'] + pass_in.apply(lambda row: string(row), axis = 1)
    pass_in['LT Date (ARR)'] = pass_in['LT Date (ARR)'].apply(datetoint) + pass_in['ATime'] * 100
    pass_in['LT Date (DEP)'] = calc_lt_date(flight_times_sg, pass_in['Orig'], pass_in['LT Date (ARR)'], 'DEP')

    pass_out['Transit'] = transit(pass_out['LT Date (DEP)'], pass_out['LT Date (ARR)'])
    pass_in['Transit'] = transit(pass_in['LT Date (DEP)'],pass_in['LT Date (ARR)'])

    pass_out['Cost'] = ''
    pass_out['Cost'] = pass_out['Cost'].apply(lambda row: cost(row, 'AIR'))
    pass_out['Carbon'] = ''
    pass_out['Carbon'] = pass_out['Carbon'].apply(lambda row: carbon(row, 'AIR'))

    pass_in['Cost'] = ''
    pass_in['Cost'] = pass_out['Cost'].apply(lambda row: cost(row, 'AIR'))
    pass_in['Carbon'] = ''
    pass_in['Carbon'] = pass_out['Carbon'].apply(lambda row: carbon(row, 'AIR'))

    ##----------------------------------PART II: Converting into Graph
    ##Implementing Dijkstra's Algorithm

    ##GENERATOR FUNCTIONS
    ##Nodes contain the name of the ports, type of port, and lat/long coordinates.
        #code - dataframe containing  names of port.
        #mode - type of port (sea / air)
        #dic - dictionary to hold all node objects.
        #lst - list to hold all node names.
        #coord - dictionary of ports lat/long coordinates.
        #remove_ports - list of nodes to remove.
        

    nodes = {}
    names = []

    def gen_nodes(code, mode, dic, lst, coord):
        for i in range(0, len(code)):
            if code[i] not in lst:
                node = Node(str(code[i]), mode)
                node.loc = coord[str(code[i])]
                dic[str(code[i])] = node
                lst.append(code[i])
            else:
                continue

    def remove_nodes(remove_ports):
        if remove_ports == None or remove_ports == []:
            return
        for port in remove_ports:
            try:
                del nodes[str(port).upper()]
            except:
                raise Exception("Port is not in dataset, or has been removed.")

            

    #The edge links two nodes together, and attaches a few values:
        # weight - transit time, $$$, carbon emissions
        # start_time - from Departs
        # end_time - from Arrives
        # vessel_code - so we know which ship to take.
        # org_code - start node
        # dep_code - destination node
        
    def gen_edges(weight, start_time, end_time, vessel_code, org_code, dep_code, cost, carbon):
        for i in range(0, len(org_code)):
            if org_code[i] in nodes.keys() and dep_code[i] in nodes.keys():
                start_node = nodes[org_code[i]]
                end_node = nodes[dep_code[i]]
                start_node.add_edge(weight[i], end_node, start_time[i], end_time[i], cost[i], carbon[i], vessel_code[i])

    def remove_edges(remove_trips):
        if remove_trips == None or remove_trips == []:
            return
        for trip in remove_trips:

            port = trip[0]
            ves = trip[1]
            date = trip[2]
            tim = trip[3]
            
            try:
                arr = int(date + tim + '00')
            except:
                raise Exception("For one of the trips to be removed, an invalid arrival date/time was given.")

            if nodes.get(port.upper(), None) == None:
                raise Exception("The port of origin of a trip you want to remove does not exist.")
            else:
                edges = nodes[port.upper()].neighbors
                for edge in edges:
                    if edge.imo == ves.upper() and edge.end_time == arr:
                        edges.remove(edge)
                        break


                


    limit = mode
    ##GENERATE SEA NODES
    if limit != 'A':
        orgport_code = ocean_df['Origin Code']
        depport_code = ocean_df['Destination Code']
        gen_nodes(orgport_code, "SEA", nodes, names, sea_coord)
        gen_nodes(depport_code, "SEA",nodes,names, sea_coord)


        start_time = ocean_df['Departs']
        end_time = ocean_df['Arrives']
        imo = ocean_df['IMO Number']
        o_cost = ocean_df['Cost']
        o_carbon = ocean_df['Carbon']

    ##GENERATE AIR NODES

    if limit != 'S':
    ##Singapore is a port for all trips, so initialise first.
        SIN = Node('SIN', 'AIR')
        nodes['SIN'] = SIN
        names.append('SIN')
        SIN.loc = air_coord['SIN']

        fout_code = freight_out['Dest & Coord. Orig/Dest Stn']
        fin_code = freight_in['Orig']
        pout_code = pass_out['Dest & Coord. Orig/Dest Stn']
        pin_code = pass_in['Orig']

        gen_nodes(fout_code, "AIR",nodes,names, air_coord)
        gen_nodes(fin_code, "AIR", nodes, names, air_coord)
        gen_nodes(pout_code, "AIR",nodes,names, air_coord)
        gen_nodes(pin_code, "AIR", nodes, names, air_coord)

    ##REMOVE user's provided nodes.
    remove_nodes(exclude_ports)
    ##----------------------------------PART III: Select Optimiser, Constraints

    ##I want the shortest transit time!
    con_ref = [float("inf"), float("inf"), float("inf")]
    for i in range(3):
        try:
            if int(constraints[i]) != 0:
                con_ref[i] = int(constraints[i])
        except:
            raise Exception("Invalid constraint values.")
        
    duration_con = con_ref[0]
    cost_con = con_ref[1]
    carbon_con = con_ref[2]


        

    ##----------------------------------PART IV: Run the Algorithm, Take User Input, Return Results
    algorithm = Dijkstra()
    
    try:
        user_start = start_port.upper()
        user_end = end_port.upper()
    except:
        raise Exception("Invalid ports.")
        

    try:
        user_depart = int(dep_date) * 1000000
    except:
        raise Exception("Invalid date.")


    try:
        connection_time = int(connection_time)
    except:
        raise Exception("Invalid connection_time.")
    
    try:
        opti = int(opti)
    except:
        raise Exception("Invalid optimiser.")

    if opti < 0 or opti > 2:
        raise Exception("Invalid optimiser.")


    if opti == 0: #time optimised
        o_weight = ocean_df['Transit']
        a_weight = 'Transit'
        connect = connection_time
    elif opti == 1: #$ optimised
        o_weight = ocean_df['Cost']
        a_weight = 'Cost'
        connect = 200
    elif opti == 2: #carbon optimised
        o_weight = ocean_df['Carbon']
        a_weight = 'Carbon'
        connect = 2



    ## Connect airports and sea ports in the same country first.
    ## Assume connection_time is 12 hours, $200 for cost, and 2 kg of carbon
    ## If land route data is provided, the above parameters can be substituted with data given.


    for key, value in codex.items():
        if key in nodes.keys() and value in nodes.keys():
            nodes[key].add_edge(connect,nodes[value], None, None, 200, 2, "Multi!")
            nodes[value].add_edge(connect,nodes[key], None, None, 200, 2, "Multi!")
            
    #Create the edges!
    #This is where the magic happens baby
    if limit != 'A':
        gen_edges(o_weight, start_time, end_time, imo, orgport_code, depport_code, o_cost, o_carbon)
    if limit != 'S':
        gen_edges(freight_out[a_weight], freight_out['LT Date (DEP)'], freight_out['LT Date (ARR)'], freight_out['Air_Code'], ['SIN',]* len(fout_code), fout_code, freight_out['Cost'], freight_out['Carbon'])
        gen_edges(freight_in[a_weight], freight_in['LT Date (DEP)'], freight_in['LT Date (ARR)'], freight_in['Air_Code'],fin_code, ['SIN',] * len(fin_code), freight_in['Cost'], freight_in['Carbon'])
        gen_edges(pass_out[a_weight], pass_out['LT Date (DEP)'], pass_out['LT Date (ARR)'], pass_out['Air_Code'], ['SIN',]* len(pout_code), pout_code, pass_out['Cost'], pass_out['Carbon'])
        gen_edges(pass_in[a_weight], pass_in['LT Date (DEP)'], pass_in['LT Date (ARR)'], pass_in['Air_Code'],pin_code, ['SIN',] * len(pin_code), pass_in['Cost'], pass_in['Carbon'])

    ##Remove user-defined trips.

    remove_edges(exclude_trips)

        
    if user_start not in nodes.keys() or user_end not in nodes.keys():
        raise Exception("Start/End Ports selected are not found in dataset, or have been excluded by user.")
    elif len(str(user_depart)) != 14:
        raise Exception ("Invalid date.")
    else:
        graph = algorithm.calculate(nodes[user_start], user_depart, opti, duration_con, cost_con, carbon_con, connection_time)
        route_1, parameters_1 = algorithm.get_shortest_path(nodes[user_end], graph)

        def modify_route(route):
            i = 1
            info = route[i]
            org_name = route[i + 1][0]
            if info[2] == 'Multi!' and len(route) > 3:
                i += 2
                info = route[i]
                org_name = route[i+1][0]
                
            ves = info[2]
            
            end = info[0]

            for edge in nodes[org_name].neighbors:
                if edge.imo == ves and edge.end_time == end:
                    nodes[org_name].neighbors.remove(edge)

            return None

        def reset_nodes(nodes):
            for node in nodes.values():
                node.visited = False
                node.predecessor = None
                node.min_distance = float("inf")

                node.time = 0
                node.cost = 0
                node.carbon = 0

            return None

        if route_1:
            modify_route(route_1)
            reset_nodes(nodes)
            graph_2 = algorithm.calculate(nodes[user_start], user_depart, opti, duration_con, cost_con, carbon_con, connection_time)
            route_2, parameters_2 = algorithm.get_shortest_path(nodes[user_end], graph_2)
        else:
            route_2, parameters_2 = [], []

        if route_2:
            modify_route(route_2)
            reset_nodes(nodes)
            graph_3 = algorithm.calculate(nodes[user_start], user_depart, opti, duration_con, cost_con, carbon_con, connection_time)
            route_3, parameters_3 = algorithm.get_shortest_path(nodes[user_end], graph_3)
        else:
            route_3, parameters_3 = [], []
            


        #JAVASCRIPT RECEIVES THIS IF SUCCESSFUL
        FINISH = [[route_1, parameters_1], [route_2,parameters_2], [route_3, parameters_3]]

    return FINISH
    

