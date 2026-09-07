# ======================================================================
# GREEDY-EDGE VERSION: greedy edge-matching construction + neighbor-list
# restricted 2-opt + double-bridge iterated local search.
# Same local search/perturbation machinery as the ship version, but the
# initial tour is built differently, so you can A/B the two.
# ======================================================================

import sys
import time
import random

# ----------------------------------------------------------------------
# CONFIGURATION CONSTANTS
# ----------------------------------------------------------------------

TIME_LIMIT_SECONDS = 300
SAFETY_MARGIN_SECONDS = 5

# Size of each city's candidate neighbor list, used both to restrict
# 2-opt's move search AND to limit which edges greedy construction
# considers (full N^2 edge sort is wasteful; we only look at each
# city's k nearest candidates as possible tour edges).
K_NEAREST_NEIGHBORS = 12

RANDOM_SEED = None


# ----------------------------------------------------------------------
# INPUT / OUTPUT
# ----------------------------------------------------------------------


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


# ----------------------------------------------------------------------
# BASIC HELPERS
# ----------------------------------------------------------------------


def tour_length(tour, dist):
    total = 0.0
    n = len(tour)
    for i in range(n):
        a = tour[i]
        b = tour[(i + 1) % n]
        total += dist[a][b]
    return total


def build_position_array(tour):
    n = len(tour)
    position = [0] * n
    for idx, city in enumerate(tour):
        position[city] = idx
    return position


def build_neighbor_lists(n, dist, k):
    k = min(k, n - 1)
    neighbor_lists = []
    for city in range(n):
        others = [c for c in range(n) if c != city]
        others.sort(key=lambda c: dist[city][c])
        neighbor_lists.append(others[:k])
    return neighbor_lists


# ----------------------------------------------------------------------
# CONSTRUCTION: GREEDY EDGE MATCHING
# ----------------------------------------------------------------------
#
# Idea: repeatedly pick the globally cheapest candidate edge (u, v) and
# add it to the tour, as long as it doesn't give any city more than 2
# tour-edges and doesn't close a cycle early (before all N cities are
# included). Keep going until every city has exactly 2 edges, which
# forms one single tour. Uses union-find to detect "would this edge
# close a premature cycle" in near O(1).


class UnionFind:
    def __init__(self, n):
        self.parent = list(range(n))

    def find(self, x):
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, x, y):
        rx, ry = self.find(x), self.find(y)
        if rx != ry:
            self.parent[rx] = ry


def greedy_edge_tour(n, dist, neighbor_lists):
    # Candidate edges: each city's k nearest neighbors, deduplicated.
    candidate_edges = set()
    for u in range(n):
        for v in neighbor_lists[u]:
            edge = (u, v) if u < v else (v, u)
            candidate_edges.add(edge)

    sorted_edges = sorted(candidate_edges, key=lambda e: dist[e[0]][e[1]])

    degree = [0] * n
    adjacency = [[] for _ in range(n)]
    uf = UnionFind(n)
    edges_used = 0

    for u, v in sorted_edges:
        if edges_used == n:
            break
        if degree[u] >= 2 or degree[v] >= 2:
            continue
        if uf.find(u) == uf.find(v):
            continue  # would close a premature cycle

        adjacency[u].append(v)
        adjacency[v].append(u)
        degree[u] += 1
        degree[v] += 1
        uf.union(u, v)
        edges_used += 1

    # The candidate-edge set (k nearest neighbors only) usually isn't
    # enough to connect every city into one single path with exactly
    # two endpoints left. Patch remaining endpoints (degree < 2) together
    # greedily by brute-force nearest available match.
    endpoints = [c for c in range(n) if degree[c] < 2]

    while len(endpoints) > 2:
        u = endpoints[0]
        best_v = None
        best_dist = float("inf")
        for v in endpoints[1:]:
            if v == u or uf.find(u) == uf.find(v):
                continue
            if dist[u][v] < best_dist:
                best_dist = dist[u][v]
                best_v = v

        if best_v is None:
            # all remaining endpoints are in the same component except
            # ones that would close the tour early; just connect to the
            # nearest different-component endpoint we can find
            for v in endpoints[1:]:
                if uf.find(u) != uf.find(v):
                    best_v = v
                    break

        adjacency[u].append(best_v)
        adjacency[best_v].append(u)
        degree[u] += 1
        degree[best_v] += 1
        uf.union(u, best_v)

        endpoints = [c for c in range(n) if degree[c] < 2]

    # Exactly two endpoints (degree 1) should remain: close the tour.
    if len(endpoints) == 2:
        u, v = endpoints
        adjacency[u].append(v)
        adjacency[v].append(u)
        degree[u] += 1
        degree[v] += 1

    # Walk the adjacency structure to produce the tour as a city order.
    tour = [0]
    visited = [False] * n
    visited[0] = True
    current = 0
    prev = -1

    for _ in range(n - 1):
        next_city = None
        for c in adjacency[current]:
            if c != prev and not visited[c]:
                next_city = c
                break
        if next_city is None:
            # fallback: pick any unvisited city (shouldn't normally trigger)
            for c in range(n):
                if not visited[c]:
                    next_city = c
                    break

        tour.append(next_city)
        visited[next_city] = True
        prev = current
        current = next_city

    return tour


# ----------------------------------------------------------------------
# LOCAL SEARCH: 2-OPT (neighbor-list restricted)
# ----------------------------------------------------------------------


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


def local_search(tour, dist, neighbor_lists, deadline):
    position = build_position_array(tour)
    improved = True
    while improved and time.time() < deadline:
        improved = two_opt_pass(tour, dist, neighbor_lists, position, deadline)
    return tour


# ----------------------------------------------------------------------
# PERTURBATION: double bridge
# ----------------------------------------------------------------------


def double_bridge(tour):
    n = len(tour)
    if n < 8:
        new_tour = tour[:]
        i, j = sorted(random.sample(range(n), 2))
        new_tour[i:j] = reversed(new_tour[i:j])
        return new_tour

    positions = sorted(random.sample(range(1, n), 3))
    p1, p2, p3 = positions

    A = tour[:p1]
    B = tour[p1:p2]
    C = tour[p2:p3]
    D = tour[p3:]

    return A + C + B + D


# ----------------------------------------------------------------------
# MAIN
# ----------------------------------------------------------------------


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

    tour = greedy_edge_tour(n, dist, neighbor_lists)
    print_tour(tour)

    tour = local_search(tour, dist, neighbor_lists, deadline)
    print_tour(tour)

    best_tour = tour[:]
    best_len = tour_length(best_tour, dist)

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
