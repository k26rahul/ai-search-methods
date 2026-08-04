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

neighbors = {
    'A': '00101',
    'B': '11101',
    'C': '10001',
    'D': '10111',
    'E': '10100'
}

# h is the number of satisfied clauses. Higher is better.
# Sort criteria: -h (descending), then label string (ascending)
sorted_neighbors = sorted(neighbors.items(), key=lambda x: (-evaluate(x[1]), x[0]))

print("Sorted neighbors:")
for label, string in sorted_neighbors:
    print(f"{label}: {string} (h={evaluate(string)})")

# take 2
beam = sorted_neighbors[:2]

# Format output as sorted 5 bit strings
output = sorted([x[1] for x in beam])
print("Output:", ",".join(output))
