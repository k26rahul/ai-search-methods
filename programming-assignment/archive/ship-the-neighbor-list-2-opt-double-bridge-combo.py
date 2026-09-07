# ======================================================================
# SHIP VERSION: nearest-neighbor construction + neighbor-list restricted
# 2-opt + double-bridge iterated local search. No Or-opt.
# ======================================================================

import sys
import time
import random

# ----------------------------------------------------------------------
# CONFIGURATION CONSTANTS
# ----------------------------------------------------------------------

# Total wall-clock budget for the whole program, matches assignment spec.
TIME_LIMIT_SECONDS = 300

# Seconds before TIME_LIMIT we stop searching, leaving room for the
# final print + process exit to complete safely.
SAFETY_MARGIN_SECONDS = 5

# Which city index nearest-neighbor construction starts from.
# Any value in [0, N-1] is valid.
START_CITY = 0

# Size of each city's candidate neighbor list, used to restrict which
# edges 2-opt considers swapping.
# Smaller (5-8)  -> faster sweeps, more iterations, may miss some moves.
# Larger (15-25) -> slower sweeps, closer to exhaustive-search quality.
K_NEAREST_NEIGHBORS = 12

# Fix the random seed for reproducible runs during testing/debugging.
# Set to None for a different random perturbation sequence each run.
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
# CONSTRUCTION
# ----------------------------------------------------------------------


def nearest_neighbor_tour(n, dist, start=0):
    visited = [False] * n
    tour = [start]
    visited[start] = True
    current = start

    for _ in range(n - 1):
        nearest_city = -1
        nearest_dist = float("inf")
        for city in range(n):
            if not visited[city] and dist[current][city] < nearest_dist:
                nearest_dist = dist[current][city]
                nearest_city = city
        tour.append(nearest_city)
        visited[nearest_city] = True
        current = nearest_city

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
# PERTURBATION: double bridge (4-opt move, escapes 2-opt local optima)
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

    tour = nearest_neighbor_tour(n, dist, start=START_CITY)
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
