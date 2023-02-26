import heapq
from my_time import time_correct
from datetime import datetime, timedelta

# class for Routes
class Edge:
    def __init__(self, weight, start_vertex, target_vertex, start_time, end_time, cost, carbon, imo = 'None'):
        self.weight = weight
        self.start_vertex = start_vertex
        self.target_vertex = target_vertex
        self.start_time = start_time
        self.end_time = end_time
        self.imo = str(imo)
        
        ##CONSTRAINTS
        self.cost = cost
        self.carbon = carbon

# class for Ports
class Node:
    def __init__(self, name, mode = None, loc = None):
        self.name = name
        self.visited = False
        # previous node that we arrived to self node from
        self.predecessor = None
        self.neighbors = [] #contains all trips that can be taken from this port.
        self.min_distance = float("inf")
        self.mode = mode
        self.loc = None

        ##CONSTRAINTS
        self.time = 0 #tracks date of arrival
        self.cost = 0
        self.carbon = 0
        
        
    def __lt__(self, other_node):
        return self.min_distance < other_node.min_distance
    
    def add_edge(self, weight, destination_vertex, start_time, end_time, cost, carbon, imo):
        edge = Edge(weight, self, destination_vertex, start_time, end_time,cost, carbon, imo)
        self.neighbors.append(edge)


# Dijkstra Algorithm
class Dijkstra:
    def __init__(self):
        self.heap = []
    
    def calculate(self, start_vertex, start_time, opti, duration_con, cost_con, carbon_con, connection_time):
        start_vertex.min_distance = 0
        start_vertex.time = start_time
        heapq.heappush(self.heap, start_vertex)
        
        total_time = {} #tracks accumulated duration at each node
        total_time[start_vertex.name] = 0

        
        route_data = {} #stores route information. Key is {prev. node ---> dest. node}

        ##CONSTRAINTS
        duration = 0
        cost = 0
        carbon = 0

        
        while self.heap:
            # pop element with the lowest distance
            actual_vertex = heapq.heappop(self.heap)
            if actual_vertex.visited:
                continue
            #  consider the neighbors
            for edge in actual_vertex.neighbors:
                start = edge.start_vertex
                target = edge.target_vertex
                new_distance = start.min_distance + edge.weight
                
                if edge.imo == 'Multi!': #we assume that costs of switching from airport to seaport is negligible. (2 minutes)
                    edge.start_time = start.time + 100
                    edge.end_time = int((datetime.strptime(str(start.time),"%Y%m%d%H%M%S") + timedelta(days = connection_time / 24)).strftime("%Y%m%d%H%M%S"))

                time_check = round((datetime.strptime(str(edge.end_time), "%Y%m%d%H%M%S") - datetime.strptime(str(start.time), "%Y%m%d%H%M%S")).total_seconds() / 3600,2)
                # time_check: a voyage can be short, but if it takes a year to depart, we shouldn't wait for it.

                if opti == 0: #time optimised
                    
                    if  time_check + total_time[start.name] < target.min_distance and start.time < edge.start_time:

                        duration = time_check + total_time[start.name]
                        cost = edge.cost + start.cost
                        carbon = edge.carbon + start.carbon
                        
                        if duration <= duration_con * 24 and cost <= cost_con and carbon <= carbon_con:

                            #store the details of the route
                            if edge.imo == 'Multi!':
                                info = (edge.end_time, edge.start_time, edge.imo, time_check, time_check, round(edge.cost,2), round(edge.carbon,2), 'switch!')
                            else:
                                info = (edge.end_time, edge.start_time, edge.imo, time_check, time_check, round(edge.cost,2), round(edge.carbon,2), start.mode)

                            route_data[start.name, target.name] = info
      
                            target.min_distance = time_check + total_time[start.name]
                            total_time[target.name] = target.min_distance
                            
                            target.time = edge.end_time
                            target.cost = cost
                            target.carbon = carbon
                            
                            target.predecessor = start
                            heapq.heappush(self.heap, target)
                
                elif new_distance < target.min_distance and start.time < edge.start_time: #cost, carbon optimised
                    duration = time_check + total_time[start.name]
                    cost = edge.cost + start.cost
                    carbon = edge.carbon + start.carbon

                    if duration <= duration_con * 24 and cost <= cost_con and carbon <= carbon_con:
                        
                        if edge.imo == 'Multi!':
                            info = (edge.end_time,edge.start_time, edge.imo, edge.weight, time_check, round(edge.cost,2), round(edge.carbon,2), 'switch!')
                        else:
                            info = (edge.end_time,edge.start_time, edge.imo, edge.weight, time_check, round(edge.cost,2), round(edge.carbon,2), start.mode)

                        route_data[start.name, target.name] = info

                        total_time[target.name] = duration
                        target.min_distance = new_distance
                        
                        target.time = edge.end_time
                        target.cost = cost
                        target.carbon = carbon
                        
                        target.predecessor = start
                        heapq.heappush(self.heap, target)

            
            actual_vertex.visited = True
            
        return route_data
    
    def get_shortest_path(self, vertex,graph):
        route = []
        parameters = []
        

        if vertex.min_distance == float("inf"):
            return [[],[]]
        else:
            parameters.append(vertex.min_distance)
            
        actual_vertex = vertex
        end_time = actual_vertex.time
        while actual_vertex is not None:
            prev = actual_vertex.name
            #print destination node's name and lat/long coordinates
            route.append((prev,actual_vertex.loc))
            actual_vertex = actual_vertex.predecessor
            #print the route from previous node to destination node
            route.append(graph[actual_vertex.name,prev])
            if actual_vertex.predecessor is None:
                #print the previous node's name and lat/long coordinates
                route.append((actual_vertex.name, actual_vertex.loc))
                start_time = actual_vertex.time
                break

        #calculate total parameters
        duration = str(round(time_correct((end_time - start_time) / 1000000, start_time, end_time),4))
        days = None
        hours = None
        for i in range(0,len(duration)):
            if duration[i] == '.':
                days = duration[:i]
                hours = duration[i+1:i+5]
                if len(hours) == 3:
                    hours += '0'
                break
        cost = round(vertex.cost,2)
        carbon = round(vertex.carbon,2)
        

        #print total parameters
        parameters.extend([(days,hours),cost,carbon])
        return [route, parameters]


