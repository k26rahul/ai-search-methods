import sys
import time
import random


def read_input():
    data = sys.stdin.read().split("\n")
    idx = 0

    kind = data[idx].strip()  # "EUCLIDEAN" or "NON-EUCLIDEAN"
    idx += 1

    n = int(data[idx].strip())
    idx += 1

    coords = []
    for i in range(n):
        parts = data[idx].split()
        coords.append((float(parts[0]), float(parts[1])))
        idx += 1

    dist = []
    for i in range(n):
        parts = data[idx].split()
        row = [float(x) for x in parts]
        dist.append(row)
        idx += 1

    return kind, n, coords, dist


def tour_length(tour, dist):
    total = 0.0
    n = len(tour)
    for i in range(n):
        a = tour[i]
        b = tour[(i + 1) % n]  # wraps back to start
        total += dist[a][b]
    return total


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


def two_opt(tour, dist, deadline):
    n = len(tour)
    improved = True

    while improved and time.time() < deadline:
        improved = False
        for i in range(n - 1):
            if time.time() > deadline:
                break
            for j in range(i + 2, n):
                if i == 0 and j == n - 1:
                    continue  # would reverse the whole tour, no-op

                a, b = tour[i], tour[i + 1]
                c, d = tour[j], tour[(j + 1) % n]

                old_cost = dist[a][b] + dist[c][d]
                new_cost = dist[a][c] + dist[b][d]

                if new_cost < old_cost - 1e-9:
                    tour[i + 1 : j + 1] = reversed(tour[i + 1 : j + 1])
                    improved = True

    return tour


def print_tour(tour):
    print(" ".join(str(city) for city in tour))
    sys.stdout.flush()


def main():
    start_time = time.time()
    TIME_LIMIT = 300
    SAFETY_MARGIN = 5  # stop working a bit before the hard cutoff
    deadline = start_time + TIME_LIMIT - SAFETY_MARGIN

    kind, n, coords, dist = read_input()

    if n == 1:
        print_tour([0])
        return

    # Step 1: construct an initial tour, print it immediately
    tour = nearest_neighbor_tour(n, dist, start=0)
    print_tour(tour)

    # Step 2: improve with 2-opt until no improvement or time runs out
    tour = two_opt(tour, dist, deadline)
    print_tour(tour)

    # Step 3: keep improving via random restarts / perturbation
    best_tour = tour[:]
    best_len = tour_length(best_tour, dist)

    while time.time() < deadline:
        # perturb: pick a random segment and reverse it (a "kick")
        new_tour = best_tour[:]
        i, j = sorted(random.sample(range(n), 2))
        new_tour[i:j] = reversed(new_tour[i:j])

        new_tour = two_opt(new_tour, dist, deadline)
        new_len = tour_length(new_tour, dist)

        if new_len < best_len:
            best_len = new_len
            best_tour = new_tour
            print_tour(best_tour)

    # final guaranteed print, in case nothing above printed after some edit
    print_tour(best_tour)


if __name__ == "__main__":
    main()
