import importlib.util
import os

# Load graph from ga3-group1.py
script_dir = os.path.dirname(os.path.abspath(__file__))
ga3_path = os.path.join(script_dir, "ga3-group1.py")
spec = importlib.util.spec_from_file_location("ga3_group1", ga3_path)
ga3_group1 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ga3_group1)

graph = ga3_group1.graph

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
