def evaluate(node):
    a = int(node[0])
    b = int(node[1])
    c = int(node[2])
    d = int(node[3])
    e = int(node[4])
    
    clauses = [
        (a or not b),
        (not a or not c),
        (not a or not e),
        (b or not e),
        (not c or d),
        (c or e)
    ]
    return sum(1 for c in clauses if c)

def get_neighbors(node):
    neighbors = []
    for i in range(5):
        flipped = '1' if node[i] == '0' else '0'
        new_node = node[:i] + flipped + node[i+1:]
        neighbors.append(new_node)
    return neighbors

open_list = ['00101', '10001']
neighbors = []

for node in open_list:
    neighbors.extend(get_neighbors(node))

print(f"Generated {len(neighbors)} neighbors")

# Evaluate and sort
# Sort by -h (descending), then label string (ascending)
scored_neighbors = [(n, evaluate(n)) for n in neighbors]
sorted_neighbors = sorted(scored_neighbors, key=lambda x: (-x[1], x[0]))

print("Sorted neighbors:")
for string, h in sorted_neighbors:
    print(f"{string}: h={h}")

# Take top 2
beam = sorted_neighbors[:2]
print(f"Top 2: {beam}")

# Get heuristic values in ascending order
h_values = sorted([x[1] for x in beam])
print(f"Output: {h_values[0]},{h_values[1]}")
