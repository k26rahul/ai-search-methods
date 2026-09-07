import random
import sys
import time

TIME_LIMIT_SECONDS = 300
SAFETY_MARGIN_SECONDS = 3
K_NEAREST_NEIGHBORS = 12
LAHC_HISTORY_LENGTH = 80
STAGNATION_RESET_LIMIT = 5000
RANDOM_SEED = None
INF = float("inf")


def read_input():
    """Read problem specification and distance matrix from standard input."""
    data = sys.stdin.read().split("\n")
    idx = 0

    kind = data[idx].strip()
    idx += 1

    n = int(data[idx].strip())
    idx += 1

    coords = []
    for _ in range(n):
        parts = data[idx].split()
        coords.append((float(parts[0]), float(parts[1])))
        idx += 1

    dist = []
    for _ in range(n):
        parts = data[idx].split()
        dist.append([float(x) for x in parts])
        idx += 1

    return kind, n, coords, dist


def print_tour(tour):
    """Write zero-based tour permutation to standard output."""
    print(" ".join(str(c) for c in tour))
    sys.stdout.flush()


def tour_length(tour, dist):
    """Calculate total closed tour cost using distance matrix."""
    n = len(tour)
    return sum(dist[tour[i]][tour[(i + 1) % n]] for i in range(n))


def build_neighbor_lists(n, dist, k):
    """Precompute k nearest neighbors for each city sorted by distance."""
    k = min(k, n - 1)
    neighbor_lists = []
    for u in range(n):
        others = [c for c in range(n) if c != u]
        others.sort(key=lambda c: dist[u][c])
        neighbor_lists.append(others[:k])
    return neighbor_lists


def build_position_array(tour):
    """Map each city index to its current position in the tour."""
    pos = [0] * len(tour)
    for idx, city in enumerate(tour):
        pos[city] = idx
    return pos


def nearest_neighbor_multistart(n, dist):
    """Evaluate nearest neighbor from all starting cities and pick shortest."""
    best_tour = None
    best_len = INF

    for start in range(n):
        visited = [False] * n
        tour = [start]
        visited[start] = True
        current = start

        for _ in range(n - 1):
            nearest_city = -1
            nearest_dist = INF
            for city in range(n):
                if not visited[city] and dist[current][city] < nearest_dist:
                    nearest_dist = dist[current][city]
                    nearest_city = city
            tour.append(nearest_city)
            visited[nearest_city] = True
            current = nearest_city

        cost = tour_length(tour, dist)
        if cost < best_len:
            best_len = cost
            best_tour = tour

    return best_tour, best_len


def farthest_insertion_tour(n, dist):
    """Build tour by iteratively inserting farthest remaining city."""
    max_d = -1.0
    c1, c2 = 0, 1
    for i in range(n):
        for j in range(i + 1, n):
            if dist[i][j] > max_d:
                max_d = dist[i][j]
                c1, c2 = i, j

    tour = [c1, c2]
    in_tour = [False] * n
    in_tour[c1] = True
    in_tour[c2] = True

    for _ in range(n - 2):
        farthest_city = -1
        max_min_d = -1.0
        for k in range(n):
            if not in_tour[k]:
                min_d = min(dist[k][c] for c in tour)
                if min_d > max_min_d:
                    max_min_d = min_d
                    farthest_city = k

        best_gain = INF
        best_pos = 0
        m = len(tour)
        for i in range(m):
            u = tour[i]
            v = tour[(i + 1) % m]
            gain = dist[u][farthest_city] + dist[farthest_city][v] - dist[u][v]
            if gain < best_gain:
                best_gain = gain
                best_pos = i + 1

        tour.insert(best_pos, farthest_city)
        in_tour[farthest_city] = True

    return tour, tour_length(tour, dist)


def greedy_edge_tour(n, dist, neighbor_lists):
    """Build tour by selecting cheapest candidate edges without premature cycles."""
    candidate_edges = set()
    for u in range(n):
        for v in neighbor_lists[u]:
            candidate_edges.add((min(u, v), max(u, v)))

    sorted_edges = sorted(candidate_edges, key=lambda e: dist[e[0]][e[1]])

    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(x, y):
        rx, ry = find(x), find(y)
        if rx != ry:
            parent[rx] = ry

    degree = [0] * n
    adj = [[] for _ in range(n)]
    edges_used = 0

    for u, v in sorted_edges:
        if edges_used == n:
            break
        if degree[u] >= 2 or degree[v] >= 2:
            continue
        if find(u) == find(v) and edges_used < n - 1:
            continue
        adj[u].append(v)
        adj[v].append(u)
        degree[u] += 1
        degree[v] += 1
        union(u, v)
        edges_used += 1

    endpoints = [c for c in range(n) if degree[c] < 2]
    while len(endpoints) > 2:
        u = endpoints[0]
        best_v = None
        best_dist = INF
        for v in endpoints[1:]:
            if find(u) != find(v) and dist[u][v] < best_dist:
                best_dist = dist[u][v]
                best_v = v
        if best_v is None:
            for v in endpoints[1:]:
                if find(u) != find(v):
                    best_v = v
                    break
        adj[u].append(best_v)
        adj[best_v].append(u)
        degree[u] += 1
        degree[best_v] += 1
        union(u, best_v)
        endpoints = [c for c in range(n) if degree[c] < 2]

    if len(endpoints) == 2:
        adj[endpoints[0]].append(endpoints[1])
        adj[endpoints[1]].append(endpoints[0])

    tour = [0]
    visited = [False] * n
    visited[0] = True
    current = 0
    prev = -1
    for _ in range(n - 1):
        next_city = None
        for c in adj[current]:
            if c != prev and not visited[c]:
                next_city = c
                break
        if next_city is None:
            for c in range(n):
                if not visited[c]:
                    next_city = c
                    break
        tour.append(next_city)
        visited[next_city] = True
        prev = current
        current = next_city

    return tour, tour_length(tour, dist)


def two_opt_pass(tour, dist, neighbor_lists, position, deadline):
    """Run one pass of neighbor-restricted 2-opt edge reversals."""
    n = len(tour)
    improved = False

    for i in range(n):
        if time.time() > deadline:
            break
        a = tour[i]
        b = tour[(i + 1) % n]
        dist_ab = dist[a][b]

        for c in neighbor_lists[a]:
            j = position[c]
            if j <= i or j == (i + 1) % n or (i == 0 and j == n - 1):
                continue
            d = tour[(j + 1) % n]

            if dist[a][c] + dist[b][d] < dist_ab + dist[c][d] - 1e-9:
                tour[i + 1 : j + 1] = reversed(tour[i + 1 : j + 1])
                for idx in range(i + 1, j + 1):
                    position[tour[idx]] = idx
                improved = True
                b = tour[(i + 1) % n]
                dist_ab = dist[a][b]

    return improved


def local_search(tour, dist, neighbor_lists, deadline):
    """Iterate 2-opt until local optimum or deadline."""
    position = build_position_array(tour)
    improved = True
    while improved and time.time() < deadline:
        improved = two_opt_pass(tour, dist, neighbor_lists, position, deadline)
    return tour


def double_bridge(tour):
    """Apply 4-opt double bridge perturbation."""
    n = len(tour)
    if n < 8:
        new_tour = tour[:]
        i, j = sorted(random.sample(range(n), 2))
        new_tour[i:j] = reversed(new_tour[i:j])
        return new_tour

    p1, p2, p3 = sorted(random.sample(range(1, n), 3))
    return tour[:p1] + tour[p2:p3] + tour[p1:p2] + tour[p3:]


def ruin_and_recreate(tour, dist, neighbor_lists, k_remove=6):
    """Remove clustered cities and reinsert using cheapest insertion."""
    n = len(tour)
    seed = random.choice(tour)
    removed = set([seed])
    for c in neighbor_lists[seed]:
        if len(removed) >= k_remove:
            break
        removed.add(c)
    while len(removed) < k_remove:
        removed.add(random.choice(tour))

    remaining = [c for c in tour if c not in removed]
    for c in removed:
        m = len(remaining)
        best_gain = INF
        best_pos = 0
        for i in range(m):
            u = remaining[i]
            v = remaining[(i + 1) % m]
            gain = dist[u][c] + dist[c][v] - dist[u][v]
            if gain < best_gain:
                best_gain = gain
                best_pos = i + 1
        remaining.insert(best_pos, c)

    return remaining


def main():
    """Main solver pipeline with construction, LAHC, and adaptive VNS."""
    if RANDOM_SEED is not None:
        random.seed(RANDOM_SEED)

    start_time = time.time()
    deadline = start_time + TIME_LIMIT_SECONDS - SAFETY_MARGIN_SECONDS

    kind, n, coords, dist = read_input()

    if n <= 1:
        print_tour([0])
        return
    if n == 2:
        print_tour([0, 1])
        return

    k_nn = min(K_NEAREST_NEIGHBORS, n - 1)
    neighbor_lists = build_neighbor_lists(n, dist, k_nn)

    # Initial construction: evaluate multiple fast heuristics
    t_nn, c_nn = nearest_neighbor_multistart(n, dist)
    t_ge, c_ge = greedy_edge_tour(n, dist, neighbor_lists)

    candidates = [(c_nn, t_nn), (c_ge, t_ge)]
    if kind.upper() == "EUCLIDEAN":
        t_fi, c_fi = farthest_insertion_tour(n, dist)
        candidates.append((c_fi, t_fi))

    candidates.sort(key=lambda x: x[0])
    best_tour = candidates[0][1][:]
    best_cost = candidates[0][0]

    # Emit first valid tour immediately
    print_tour(best_tour)

    # Optimize initial constructions with local search
    for _, tour in candidates:
        if time.time() >= deadline:
            break
        opt_tour = local_search(tour[:], dist, neighbor_lists, deadline)
        opt_cost = tour_length(opt_tour, dist)
        if opt_cost < best_cost - 1e-9:
            best_cost = opt_cost
            best_tour = opt_tour[:]
            print_tour(best_tour)

    curr_tour = best_tour[:]
    curr_cost = best_cost

    history = [curr_cost] * LAHC_HISTORY_LENGTH
    h_ptr = 0
    stagnation_count = 0

    # Main metaheuristic loop: LAHC with Double Bridge and Ruin & Recreate
    while time.time() < deadline:
        if random.random() < 0.82:
            candidate = double_bridge(curr_tour)
        else:
            k = random.randint(4, min(10, max(4, n // 4)))
            candidate = ruin_and_recreate(curr_tour, dist, neighbor_lists, k_remove=k)

        candidate = local_search(candidate, dist, neighbor_lists, deadline)
        cand_cost = tour_length(candidate, dist)

        if cand_cost <= curr_cost or cand_cost <= history[h_ptr]:
            curr_tour = candidate[:]
            curr_cost = cand_cost

        history[h_ptr] = curr_cost
        h_ptr = (h_ptr + 1) % LAHC_HISTORY_LENGTH

        if cand_cost < best_cost - 1e-9:
            best_cost = cand_cost
            best_tour = candidate[:]
            stagnation_count = 0
            print_tour(best_tour)
        else:
            stagnation_count += 1
            if stagnation_count >= STAGNATION_RESET_LIMIT:
                curr_tour = best_tour[:]
                curr_cost = best_cost
                history = [best_cost] * LAHC_HISTORY_LENGTH
                stagnation_count = 0

    print_tour(best_tour)


if __name__ == "__main__":
    main()
