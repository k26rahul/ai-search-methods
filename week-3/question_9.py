import importlib.util
import os
import math

# Load graph from ga3-group1.py
script_dir = os.path.dirname(os.path.abspath(__file__))
ga3_path = os.path.join(script_dir, "ga3-group1.py")
spec = importlib.util.spec_from_file_location("ga3_group1", ga3_path)
ga3_group1 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ga3_group1)

graph = ga3_group1.graph

def euclidean_distance(loc1, loc2):
    return math.sqrt((loc1[0] - loc2[0])**2 + (loc1[1] - loc2[1])**2)

start_node = 'S'
tour = [start_node]
visited = {start_node}
current_node = start_node
num_cities = len(graph)

failed = False

while len(tour) < num_cities:
    neighbors = graph[current_node].neighbors
    unvisited_neighbors = [n for n in neighbors if n not in visited]
    
    if not unvisited_neighbors:
        failed = True
        break
        
    best_dist = float('inf')
    best_node = None
    
    for n in sorted(unvisited_neighbors):
        dist = euclidean_distance(graph[current_node].location, graph[n].location)
        if dist < best_dist:
            best_dist = dist
            best_node = n
            
    current_node = best_node
    tour.append(current_node)
    visited.add(current_node)

if not failed:
    if start_node in graph[current_node].neighbors:
        tour.append(start_node)
    else:
        failed = True

if failed:
    print("Nearest Neighbour algorithm fails to find a tour")
    print(f"Path until failure: {tour}")
else:
    print("Nearest Neighbour algorithm finds a tour")
    print(f"Tour: {tour}")
