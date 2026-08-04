from graph_data import graph

def manhattan_distance(loc1, loc2):
    return abs(loc1[0] - loc2[0]) + abs(loc1[1] - loc2[1])

if __name__ == "__main__":
    goal_node = 'G'
    goal_loc = graph[goal_node].location

    max_h = -1
    max_node = None

    for node_id, node in sorted(graph.items()):
        h = manhattan_distance(node.location, goal_loc)
        if h > max_h:
            max_h = h
            max_node = node_id

    # Print in the requested format
    print(f"{max_node},{max_h}")
