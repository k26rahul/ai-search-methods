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

valid_assignments = []
for i in range(32):
    # Convert i to 5-bit binary string
    node = f"{i:05b}"
    if evaluate(node) == 6:
        valid_assignments.append(node)

print(f"Found {len(valid_assignments)} solutions:")
for sol in valid_assignments:
    print(sol)
