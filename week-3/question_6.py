from graph_data import graph

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
