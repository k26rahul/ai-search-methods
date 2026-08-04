# Week 3 Assignment Solutions

**Question 1: BFS Node Inspection Order**

```
S,B,E,J,O,A,F
```

**Question 2: Node with largest heuristic value (Manhattan distance to G)**

```
B,16
```

**Question 3: Best First Search Inspection Order**

```
S,J,I,E,F,K,M
```

**Question 4: Hill Climbing node sequence**

```
S,J,I
```

**Question 5: Hill Climbing node sequence (Extended)**

```
S,J,I,J,I,J,I
```

**Question 6: Local Optimum Node**

```
I
```

**Question 7: Modified Question Path**
Answer: S,B,A,C,D,G

**Question 8: Number of Hamiltonian Cycles**

```
Node S: degree 4
Node A: degree 4
Node B: degree 3
Node C: degree 3
Node D: degree 3
Node E: degree 5
Node F: degree 4
Node G: degree 4
Node H: degree 3
Node I: degree 2
Node J: degree 3
Node K: degree 3
Node L: degree 3
Node M: degree 4
Node N: degree 4
Node O: degree 3
Node P: degree 3
Number of Hamiltonian cycles found: 22
```

**Question 9: Nearest Neighbour Heuristic**

```
Nearest Neighbour algorithm fails to find a tour
Path until failure: ['S', 'J', 'I', 'E', 'B', 'A', 'C', 'D', 'G', 'M', 'K', 'F']
```

**Question 10: Greedy Heuristic**

```
Greedy algorithm fails to find a tour
Edges added: 15
[('I', 'J'), ('B', 'E'), ('G', 'M'), ('H', 'L'), ('A', 'C'), ('C', 'D'), ('E', 'F'), ('F', 'K'), ('G', 'L'), ('J', 'S'), ('K', 'M'), ('A', 'B'), ('N', 'O'), ('O', 'S'), ('N', 'P')]
```

**Question 11: SAT Heuristic Values for S, D, E**

```
S: 2
A: 4
B: 3
C: 4
D: 3
E: 4
```

**Question 12: Beam Search (w=2) Level 2 Nodes**

```
Sorted neighbors:
A: 00101 (h=4)
C: 10001 (h=4)
E: 10100 (h=4)
B: 11101 (h=3)
D: 10111 (h=3)
Output: 00101,10001
```

**Question 13: Beam Search (w=2) Level 3 Node Heuristic Values**

```
Generated 10 neighbors
Sorted neighbors:
00001: h=5
00001: h=5
00100: h=5
00111: h=5
10000: h=5
11001: h=5
01101: h=4
10011: h=4
10101: h=2
10101: h=2
Top 2: [('00001', 5), ('00001', 5)]
Output: 5,5
```

**Question 14: Exact Variable Assignment for SAT formula**

```
Found 1 solutions:
00110
```

**Question 15: Select the correct statements**
Answer: A, D

**Question 16: Complete algorithms for finite state/solution space**
Answer: A, B, C

**Question 17: Working with 2-City-Exchange operator**
Answer: C, D

**Question 18: Iterated Hill Climbing algorithm**
Answer: B, E

**Question 19: Why Hill Climbing may run into a local optimum**
Answer: C

**Question 20: Variable Neighbourhood Descent**
Answer: A, C
