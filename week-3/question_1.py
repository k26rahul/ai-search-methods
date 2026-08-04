from graph_data import graph

def bfs(graph, start_node, goal_node, max_inspected=7):
    # OPEN <- (S, null) : []
    open_list = [(start_node, None)]
    # CLOSED <- empty list
    closed_list = []
    
    inspected = []

    # while OPEN is not empty
    while open_list:
        # nodePair <- head OPEN
        node_pair = open_list[0]
        # (N, _) <- nodePair
        node = node_pair[0]
        
        # Track inspected nodes
        inspected.append(node)
        
        if len(inspected) == max_inspected:
            break
            
        # if GoalTest(N) == true
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
                
        # newPairs <- MakePairs(newNodes, N)
        new_pairs = [(n, node) for n in new_nodes]
        
        # OPEN <- (tail OPEN) ++ newPairs
        open_list = open_list[1:] + new_pairs

    return inspected

if __name__ == "__main__":
    result = bfs(graph, 'S', 'G', max_inspected=7)
    print(",".join(result))
