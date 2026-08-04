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

# Collect all unique edges
edges = []
for u in graph:
    for v in graph[u].neighbors:
        if u < v:
            dist = euclidean_distance(graph[u].location, graph[v].location)
            edges.append((dist, u, v))

# Sort edges by cost, then by node labels
edges.sort(key=lambda x: (x[0], x[1], x[2]))

parent = {node: node for node in graph}

def find(i):
    if parent[i] == i:
        return i
    parent[i] = find(parent[i])
    return parent[i]

def union(i, j):
    root_i = find(i)
    root_j = find(j)
    if root_i != root_j:
        parent[root_i] = root_j

degree = {node: 0 for node in graph}
tour_edges = []
n_nodes = len(graph)

for dist, u, v in edges:
    if degree[u] < 2 and degree[v] < 2:
        if find(u) != find(v):
            tour_edges.append((u, v))
            degree[u] += 1
            degree[v] += 1
            union(u, v)
        elif len(tour_edges) == n_nodes - 1:
            # Last edge to close the loop
            tour_edges.append((u, v))
            degree[u] += 1
            degree[v] += 1
            break

if len(tour_edges) == n_nodes:
    print("Greedy algorithm finds a tour")
    print(tour_edges)
else:
    print("Greedy algorithm fails to find a tour")
    print(f"Edges added: {len(tour_edges)}")
    print(tour_edges)
