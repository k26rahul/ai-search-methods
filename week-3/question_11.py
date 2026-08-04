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

nodes = {
    'S': '10101',
    'A': '00101',
    'B': '11101',
    'C': '10001',
    'D': '10111',
    'E': '10100'
}

for name, val in nodes.items():
    print(f"{name}: {evaluate(val)}")
