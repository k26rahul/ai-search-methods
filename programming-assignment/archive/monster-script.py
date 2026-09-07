import sys
import time
import random

# ======================================================================
# CONFIGURATION CONSTANTS
# Tune these to change solver behaviour. Comments explain what each
# does and reasonable alternative values to try.
# ======================================================================

# Total wall-clock budget for the whole program, matches assignment spec.
TIME_LIMIT_SECONDS = 300

# How many seconds before TIME_LIMIT we stop searching, to leave room
# for the final print + process exit to complete safely.
# Increase if you see timeouts in grading; decrease to squeeze more search time.
SAFETY_MARGIN_SECONDS = 5

# Which city index the nearest-neighbor construction starts from.
# Any value in [0, N-1] is valid. 0 is simplest; could also randomize.
START_CITY = 0

# Size of each city's candidate neighbor list, used to restrict which
# edges 2-opt and Or-opt consider swapping/inserting.
# Smaller (5-8)  -> faster sweeps, more iterations, may miss some moves.
# Larger (15-25) -> slower sweeps, closer to full/exhaustive search quality.
K_NEAREST_NEIGHBORS = 12

# Longest segment length Or-opt will try to relocate (moves chains of
# 1..OR_OPT_MAX_SEGMENT consecutive cities to a better position).
# Typical range: 1 to 3. Higher values cost more time per sweep.
OR_OPT_MAX_SEGMENT = 3

# Whether to run Or-opt at all. Turning this off falls back to pure 2-opt,
# useful for isolating/debugging behaviour or for very large N where
# Or-opt's O(N) move cost becomes too expensive.
USE_OR_OPT = True

# After local search converges (no more 2-opt/Or-opt improvement found),
# whether to keep exploring via double-bridge perturbation + re-optimization
# (classic Iterated Local Search) instead of stopping.
USE_ITERATED_LOCAL_SEARCH = True

# Fix the random seed for reproducible runs during testing/debugging.
# Set to None for a different random perturbation sequence each run.
RANDOM_SEED = None


# ======================================================================
# INPUT / OUTPUT
# ======================================================================


def read_input():
    data = sys.stdin.read().split("\n")
    idx = 0

    kind = data[idx].strip()  # "EUCLIDEAN" or "NON-EUCLIDEAN"
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
    """
    For each city, precompute its k nearest cities by distance.
    2-opt and Or-opt only consider reconnecting/inserting near these
    cities instead of scanning all N-1 others every time.
    """
    k = min(k, n - 1)
    neighbor_lists = []
    for city in range(n):
        others = [c for c in range(n) if c != city]
        others.sort(key=lambda c: dist[city][c])
        neighbor_lists.append(others[:k])
    return neighbor_lists


# ======================================================================
# CONSTRUCTION
# ======================================================================


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


# ======================================================================
# LOCAL SEARCH: 2-OPT (neighbor-list restricted)
# ======================================================================


def two_opt_pass(tour, dist, neighbor_lists, position, deadline):
    """
    One full sweep of neighbor-list restricted 2-opt.
    Mutates tour and position in place. Returns True if any
    improving move was applied during this sweep.
    """
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
                continue  # would reverse the whole tour, no-op

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
# LOCAL SEARCH: OR-OPT (relocate short segments)
# ======================================================================


def or_opt_pass(tour, dist, neighbor_lists, position, deadline, max_segment):
    """
    One full sweep of Or-opt: try relocating short chains of consecutive
    cities (length 1..max_segment) to a better spot elsewhere in the tour,
    optionally reversed. Complements 2-opt, which cannot perform relocations.
    Mutates tour and position in place. Returns True if any improving
    move was applied during this sweep.
    """
    n = len(tour)
    improved_any = False

    for seg_len in range(1, max_segment + 1):
        if n - seg_len < 3:
            continue  # not enough cities left outside the segment

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
                continue  # removing this segment doesn't shrink the tour

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

                add_forward = dist[a][s_first] + dist[s_last][b]
                gain_forward = removed_gain + base - add_forward
                if gain_forward > best_gain:
                    best_gain = gain_forward
                    best_insert_city = a
                    best_reversed = False

                add_reversed = dist[a][s_last] + dist[s_first][b]
                gain_reversed = removed_gain + base - add_reversed
                if gain_reversed > best_gain:
                    best_gain = gain_reversed
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
# LOCAL SEARCH DRIVER: alternate 2-opt and Or-opt until no improvement
# ======================================================================


def local_search(tour, dist, neighbor_lists, deadline):
    position = build_position_array(tour)

    improved = True
    while improved and time.time() < deadline:
        improved_2opt = two_opt_pass(tour, dist, neighbor_lists, position, deadline)

        improved_oropt = False
        if USE_OR_OPT and time.time() < deadline:
            improved_oropt = or_opt_pass(
                tour, dist, neighbor_lists, position, deadline, OR_OPT_MAX_SEGMENT
            )

        improved = improved_2opt or improved_oropt

    return tour


# ======================================================================
# PERTURBATION: double bridge (4-opt move, escapes 2-opt/Or-opt optima)
# ======================================================================


def double_bridge(tour):
    """
    Cut the tour into 4 segments A B C D and reconnect as A C B D.
    Unlike a plain segment reversal, this cannot be undone by a single
    2-opt or Or-opt move, so it forces real exploration of new regions
    of the search space.
    """
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

    # Step 1: construct an initial tour, print immediately so a valid
    # answer exists on stdout as early as possible.
    tour = nearest_neighbor_tour(n, dist, start=START_CITY)
    print_tour(tour)

    # Step 2: local search (2-opt + Or-opt) to a local optimum.
    tour = local_search(tour, dist, neighbor_lists, deadline)
    print_tour(tour)

    best_tour = tour[:]
    best_len = tour_length(best_tour, dist)

    # Step 3: Iterated Local Search — perturb with double bridge,
    # re-run local search, keep the result only if it's better.
    if USE_ITERATED_LOCAL_SEARCH:
        while time.time() < deadline:
            candidate = double_bridge(best_tour)
            candidate = local_search(candidate, dist, neighbor_lists, deadline)
            candidate_len = tour_length(candidate, dist)

            if candidate_len < best_len - 1e-9:
                best_len = candidate_len
                best_tour = candidate
                print_tour(best_tour)

    # Final guaranteed print in case nothing printed near the very end.
    print_tour(best_tour)


if __name__ == "__main__":
    main()
