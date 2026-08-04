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

def hill_climbing(start_node, goal_node, max_inspected=7):
    n = start_node
    inspected = []
    
    while True:
        best_ever = n
        inspected.append(best_ever)
        
        if best_ever == goal_node or len(inspected) == max_inspected:
            break
            
        neighbours = graph[best_ever].neighbors
        
        # sorth MoveGen(bestEver)
        sorted_neighbours = sorted(neighbours, key=lambda x: (h(x), x))
        
        # N <- head sorth MoveGen(bestEver)
        if not sorted_neighbours:
            break
        n = sorted_neighbours[0]
        
        # while h(N) is better than h(bestEver)
        if not (h(n) < h(best_ever)):
            break
            
    return inspected

if __name__ == "__main__":
    result = hill_climbing('S', 'G', max_inspected=7)
    print(",".join(result))
