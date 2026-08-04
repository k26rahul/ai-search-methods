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

def best_first_search(start_node, goal_node, max_inspected=7):
    # OPEN <- (S, null, h(S)) : []
    open_list = [(start_node, None, h(start_node))]
    closed_list = []
    
    inspected = []

    while open_list:
        # nodePair <- head OPEN
        node_pair = open_list[0]
        node = node_pair[0]
        
        inspected.append(node)
        
        if len(inspected) == max_inspected:
            break
            
        if node == goal_node:
            break
            
        # else CLOSED <- nodePair : CLOSED
        closed_list.insert(0, node_pair)
        
        # neighbours <- MoveGen(N)
        neighbours = graph[node].neighbors
        
        # newNodes <- RemoveSeen(neighbours, OPEN, CLOSED)
        new_nodes = []
        for n in neighbours:
            in_open = any(p[0] == n for p in open_list)
            in_closed = any(p[0] == n for p in closed_list)
            if not in_open and not in_closed:
                new_nodes.append(n)
                
        # newPairs <- MakePairs(...)
        new_pairs = [(n, node, h(n)) for n in new_nodes]
        
        # OPEN <- sorth(newPairs ++ tail OPEN)
        tail_open = open_list[1:]
        combined = new_pairs + tail_open
        # sorth sorts by h(N) then alphabetically
        open_list = sorted(combined, key=lambda x: (x[2], x[0]))

    return inspected

if __name__ == "__main__":
    result = best_first_search('S', 'G', max_inspected=7)
    print(",".join(result))
