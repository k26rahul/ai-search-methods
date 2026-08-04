from graph_data import graph

def find_all_hamiltonian_cycles(graph):
    nodes = list(graph.keys())
    n = len(nodes)
    start_node = nodes[0]
    
    cycles = []
    
    def backtrack(curr_node, visited, path):
        if len(path) == n:
            if start_node in graph[curr_node].neighbors:
                cycles.append(path + [start_node])
            return
            
        for neighbor in graph[curr_node].neighbors:
            if neighbor not in visited:
                visited.add(neighbor)
                path.append(neighbor)
                backtrack(neighbor, visited, path)
                path.pop()
                visited.remove(neighbor)

    backtrack(start_node, {start_node}, [start_node])
    return cycles

if __name__ == "__main__":
    for node_id, node in graph.items():
        print(f"Node {node_id}: degree {len(node.neighbors)}")
        
    cycles = find_all_hamiltonian_cycles(graph)
    print(f"Number of Hamiltonian cycles found: {len(cycles)}")
