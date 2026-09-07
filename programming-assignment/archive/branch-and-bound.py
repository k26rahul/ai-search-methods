import sys
import time
import random

TIME_LIMIT_SECONDS = 300
SAFETY_MARGIN_SECONDS = 5
K_NEAREST_NEIGHBORS = 15
OR_OPT_MAX_SEGMENT = 3
RANDOM_SEED = None
INF = float("inf")


# ======================================================================
# INPUT / OUTPUT
# ======================================================================


def read_input():
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
        row = [float(x) for x in parts]
        dist.append(row)
        idx += 1

    return kind, n, coords, dist


def print_tour(tour):
    print(" ".join(str(city) for city in tour))
    sys.stdout.flush()


# ======================================================================
# BASIC HELPERS
# ======================================================================


def tour_length(tour, dist):
    total = 0.0
    n = len(tour)
    for i in range(n):
        total += dist[tour[i]][tour[(i + 1) % n]]
    return total


def build_neighbor_lists(n, dist, k):
    k = min(k, n - 1)
    neighbor_lists = []
    for city in range(n):
        others = list(range(n))
        others.remove(city)
        others.sort(key=lambda c: dist[city][c])
        neighbor_lists.append(others[:k])
    return neighbor_lists


def build_position_array(tour):
    position = [0] * len(tour)
    for idx, city in enumerate(tour):
        position[city] = idx
    return position


# ======================================================================
# CONSTRUCTION HEURISTICS
# ======================================================================


def nearest_neighbor_tour(n, dist, start=0):
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

    return tour


def greedy_edge_tour(n, dist, neighbor_lists):
    """Greedy edge construction using candidate edges from neighbor lists."""
    candidate_edges = set()
    for u in range(n):
        for v in neighbor_lists[u]:
            edge = (u, v) if u < v else (v, u)
            candidate_edges.add(edge)

    sorted_edges = sorted(candidate_edges, key=lambda e: dist[e[0]][e[1]])

    degree = [0] * n
    adj = [[] for _ in range(n)]
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
            if v == u or find(u) == find(v):
                continue
            if dist[u][v] < best_dist:
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
        u, v = endpoints
        adj[u].append(v)
        adj[v].append(u)

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

    return tour


# ======================================================================
# LOCAL SEARCH: 2-OPT (neighbor-list restricted)
# ======================================================================


def two_opt_pass(tour, dist, neighbor_lists, position, deadline):
    n = len(tour)
    improved_any = False

    for i in range(n):
        if time.time() > deadline:
            break

        a = tour[i]
        b = tour[(i + 1) % n]
        dist_ab = dist[a][b]

        for c in neighbor_lists[a]:
            j = position[c]
            if j <= i or j == (i + 1) % n:
                continue
            if i == 0 and j == n - 1:
                continue

            d = tour[(j + 1) % n]
            old_cost = dist_ab + dist[c][d]
            new_cost = dist[a][c] + dist[b][d]

            if new_cost < old_cost - 1e-9:
                tour[i + 1 : j + 1] = reversed(tour[i + 1 : j + 1])
                for idx in range(i + 1, j + 1):
                    position[tour[idx]] = idx
                improved_any = True
                b = tour[(i + 1) % n]
                dist_ab = dist[a][b]

    return improved_any


# ======================================================================
# LOCAL SEARCH: OR-OPT
# ======================================================================


def or_opt_pass(tour, dist, neighbor_lists, position, deadline, max_segment):
    n = len(tour)
    improved_any = False

    for seg_len in range(1, max_segment + 1):
        if n - seg_len < 3:
            continue

        for i in range(n):
            if time.time() > deadline:
                return improved_any

            seg_indices = [(i + k) % n for k in range(seg_len)]
            if len(set(seg_indices)) < seg_len:
                continue

            prev_idx = (i - 1) % n
            next_idx = (i + seg_len) % n
            if prev_idx in seg_indices or next_idx in seg_indices:
                continue

            seg = [tour[x] for x in seg_indices]
            p = tour[prev_idx]
            q = tour[next_idx]
            s_first = seg[0]
            s_last = seg[-1]

            removed_gain = dist[p][s_first] + dist[s_last][q] - dist[p][q]
            if removed_gain <= 1e-9:
                continue

            candidates = set(neighbor_lists[s_first]) | set(neighbor_lists[s_last])
            best_gain = 1e-9
            best_insert_city = None
            best_reversed = False

            for c in candidates:
                j = position[c]
                if j in seg_indices:
                    continue
                j_next = (j + 1) % n
                if j_next in seg_indices:
                    continue

                a = tour[j]
                b = tour[j_next]
                base = dist[a][b]

                add_fwd = dist[a][s_first] + dist[s_last][b]
                gain_fwd = removed_gain + base - add_fwd
                if gain_fwd > best_gain:
                    best_gain = gain_fwd
                    best_insert_city = a
                    best_reversed = False

                add_rev = dist[a][s_last] + dist[s_first][b]
                gain_rev = removed_gain + base - add_rev
                if gain_rev > best_gain:
                    best_gain = gain_rev
                    best_insert_city = a
                    best_reversed = True

            if best_insert_city is not None:
                seg_set = set(seg_indices)
                new_tour = [tour[x] for x in range(n) if x not in seg_set]
                insert_pos = new_tour.index(best_insert_city) + 1
                seg_to_insert = seg if not best_reversed else list(reversed(seg))
                new_tour[insert_pos:insert_pos] = seg_to_insert
                tour[:] = new_tour
                for idx, city in enumerate(tour):
                    position[city] = idx
                improved_any = True

    return improved_any


# ======================================================================
# COMBINED LOCAL SEARCH
# ======================================================================


def local_search(tour, dist, neighbor_lists, deadline):
    position = build_position_array(tour)
    improved = True
    while improved and time.time() < deadline:
        improved_2opt = two_opt_pass(
            tour, dist, neighbor_lists, position, deadline
        )
        improved_oropt = False
        if time.time() < deadline:
            improved_oropt = or_opt_pass(
                tour, dist, neighbor_lists, position, deadline, OR_OPT_MAX_SEGMENT
            )
        improved = improved_2opt or improved_oropt
    return tour


# ======================================================================
# PERTURBATION: DOUBLE BRIDGE
# ======================================================================


def double_bridge(tour):
    n = len(tour)
    if n < 8:
        new_tour = tour[:]
        i, j = sorted(random.sample(range(n), 2))
        new_tour[i:j] = reversed(new_tour[i:j])
        return new_tour

    positions = sorted(random.sample(range(1, n), 3))
    p1, p2, p3 = positions
    return tour[:p1] + tour[p2:p3] + tour[p1:p2] + tour[p3:]


# ======================================================================
# MAIN
# ======================================================================


def main():
    if RANDOM_SEED is not None:
        random.seed(RANDOM_SEED)

    start_time = time.time()
    deadline = start_time + TIME_LIMIT_SECONDS - SAFETY_MARGIN_SECONDS

    kind, n, coords, dist = read_input()

    if n == 1:
        print_tour([0])
        return
    if n == 2:
        print_tour([0, 1])
        return

    neighbor_lists = build_neighbor_lists(n, dist, K_NEAREST_NEIGHBORS)

    # Phase 1: Best construction heuristic (fast)
    # Multi-start nearest-neighbor picks the best among all starting cities
    best_nn_tour = None
    best_nn_len = INF

    for start in range(n):
        tour = nearest_neighbor_tour(n, dist, start)
        length = tour_length(tour, dist)
        if length < best_nn_len:
            best_nn_len = length
            best_nn_tour = tour[:]

    best_tour = best_nn_tour[:]
    best_len = best_nn_len
    print_tour(best_tour)

    # Phase 2: Local search on best construction
    best_tour = local_search(best_tour, dist, neighbor_lists, deadline)
    best_len = tour_length(best_tour, dist)
    print_tour(best_tour)

    # Phase 3: Iterated Local Search - double bridge + local search
    # Pure greedy acceptance (only keep improvements)
    while time.time() < deadline:
        candidate = double_bridge(best_tour)
        candidate = local_search(candidate, dist, neighbor_lists, deadline)
        candidate_len = tour_length(candidate, dist)

        if candidate_len < best_len - 1e-9:
            best_len = candidate_len
            best_tour = candidate
            print_tour(best_tour)

    print_tour(best_tour)


if __name__ == "__main__":
    main()
