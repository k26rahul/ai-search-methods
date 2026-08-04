import importlib.util
import os
import sys

# Load graph from ga3-group1.py
script_dir = os.path.dirname(os.path.abspath(__file__))
ga3_path = os.path.join(script_dir, "ga3-group1.py")
spec = importlib.util.spec_from_file_location("ga3_group1", ga3_path)
ga3_group1 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ga3_group1)

graph = ga3_group1.graph

def manhattan_distance(loc1, loc2):
    return abs(loc1[0] - loc2[0]) + abs(loc1[1] - loc2[1])

goal_node = 'G'
goal_loc = graph[goal_node].location

def h(node_id):
    return manhattan_distance(graph[node_id].location, goal_loc)

def best_neighbour_search(start_node, goal_node):
    n = start_node
    best_seen = start_node
    num_cities = len(graph)
    
    for _ in range(num_cities):
        if h(n) == 0:
            break
            
        neighbours = graph[n].neighbors
        
        # N <- best MoveGen(N)
        sorted_neighbours = sorted(neighbours, key=lambda x: (h(x), x))
        if not sorted_neighbours:
            break
        n = sorted_neighbours[0]
        
        # if N is better than bestSeen
        if h(n) < h(best_seen):
            best_seen = n
            
    return best_seen

if __name__ == "__main__":
    result = best_neighbour_search('S', 'G')
    print(result)
