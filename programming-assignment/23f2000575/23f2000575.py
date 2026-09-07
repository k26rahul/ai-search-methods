# Traveling Salesperson Problem (TSP) Solver using Iterated Local Search (ILS).
#
# Approach:
# - Input parsing: reads city coordinates and distance matrix from standard input.
# - Construction: builds an initial complete tour using the greedy nearest neighbor heuristic.
# - Candidate lists: precomputes k-nearest neighbors for each city to restrict 2-opt edge moves.
# - Local search: iteratively improves tour quality using candidate-restricted 2-opt swaps.
# - Perturbation: applies random segment reversals to escape local optima.
# - Search loop: alternates perturbation and local search until the wall-clock deadline expires.

import random
import sys
import time


class TSPSolver:
    """Solves the Traveling Salesperson Problem using Iterated Local Search."""

    def __init__(
        self,
        time_limit: float = 300.0,
        safety_margin: float = 5.0,
        k_neighbors: int = 12,
        start_city: int = 0,
    ):
        self.time_limit = time_limit
        self.safety_margin = safety_margin
        self.k_neighbors = k_neighbors
        self.start_city = start_city

        self.deadline = 0.0
        self.kind = ""
        self.num_cities = 0
        self.coordinates = []
        self.distance_matrix = []
        self.neighbor_candidate_lists = []

    def read_problem_from_stdin(self):
        """Reads problem specification from standard input."""
        data = sys.stdin.read().split("\n")
        idx = 0

        self.kind = data[idx].strip()  # "EUCLIDEAN" or "NON-EUCLIDEAN"
        idx += 1

        self.num_cities = int(data[idx].strip())
        idx += 1

        self.coordinates = []
        for _ in range(self.num_cities):
            parts = data[idx].split()
            self.coordinates.append((float(parts[0]), float(parts[1])))
            idx += 1

        self.distance_matrix = []
        for _ in range(self.num_cities):
            parts = data[idx].split()
            row = [float(x) for x in parts]
            self.distance_matrix.append(row)
            idx += 1

    def calculate_total_tour_length(self, tour: list[int]) -> float:
        """Calculates the total round-trip distance of a tour."""
        total = 0.0
        n = len(tour)
        dist = self.distance_matrix
        for i in range(n):
            a = tour[i]
            b = tour[(i + 1) % n]  # Wraps back to start
            total += dist[a][b]
        return total

    def construct_nearest_neighbor_tour(self, start_city: int = 0) -> list[int]:
        """Builds an initial tour using the greedy nearest neighbor heuristic."""
        n = self.num_cities
        dist = self.distance_matrix
        visited = [False] * n
        tour = [start_city]
        visited[start_city] = True
        current = start_city

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

    def build_candidate_neighbor_lists(self) -> list[list[int]]:
        """Precomputes k-nearest candidate neighbors for each city."""
        n = self.num_cities
        dist = self.distance_matrix
        k = min(self.k_neighbors, n - 1)
        neighbor_lists = []
        for city in range(n):
            others = [c for c in range(n) if c != city]
            others.sort(key=lambda c: dist[city][c])
            neighbor_lists.append(others[:k])
        return neighbor_lists

    def optimize_tour_with_restricted_two_opt(self, tour: list[int]) -> list[int]:
        """Applies 2-opt edge exchanges restricted to candidate neighbors."""
        n = len(tour)
        dist = self.distance_matrix
        neighbor_lists = self.neighbor_candidate_lists
        deadline = self.deadline

        # position[city] = index of that city in the current tour, kept in sync
        position = [0] * n
        for idx, city in enumerate(tour):
            position[city] = idx

        improved = True
        while improved and time.time() < deadline:
            improved = False
            for i in range(n):
                if time.time() > deadline:
                    break

                a = tour[i]
                b = tour[(i + 1) % n]
                dist_ab = dist[a][b]

                # Only try reconnecting 'a' to cities in its candidate list,
                # instead of every other city in the tour
                for c in neighbor_lists[a]:
                    j = position[c]
                    # Need j to be "after" i on the tour, and not adjacent
                    if j <= i or j == (i + 1) % n:
                        continue
                    if i == 0 and j == n - 1:
                        continue  # Would reverse whole tour, no-op

                    d = tour[(j + 1) % n]

                    old_cost = dist_ab + dist[c][d]
                    new_cost = dist[a][c] + dist[b][d]

                    if new_cost < old_cost - 1e-9:
                        tour[i + 1 : j + 1] = reversed(tour[i + 1 : j + 1])
                        # Positions shifted for the reversed segment; resync them
                        for idx in range(i + 1, j + 1):
                            position[tour[idx]] = idx
                        improved = True
                        b = tour[(i + 1) % n]
                        dist_ab = dist[a][b]

        return tour

    def perturb_tour_by_random_segment_reversal(self, tour: list[int]) -> list[int]:
        """Perturbs a tour by reversing a randomly chosen subsegment."""
        perturbed_tour = tour[:]
        i, j = sorted(random.sample(range(self.num_cities), 2))
        perturbed_tour[i:j] = reversed(perturbed_tour[i:j])
        return perturbed_tour

    def print_tour_to_stdout(self, tour: list[int]):
        """Prints the tour representation to standard output."""
        print(" ".join(str(city) for city in tour))
        sys.stdout.flush()

    def run_iterated_local_search(self, initial_tour: list[int]) -> list[int]:
        """Iteratively perturbs and improves the tour until the deadline."""
        best_tour = initial_tour[:]
        best_len = self.calculate_total_tour_length(best_tour)

        while time.time() < self.deadline:
            # Perturb: pick a random segment and reverse it (a "kick")
            perturbed_tour = self.perturb_tour_by_random_segment_reversal(best_tour)
            improved_tour = self.optimize_tour_with_restricted_two_opt(perturbed_tour)
            current_len = self.calculate_total_tour_length(improved_tour)

            if current_len < best_len:
                best_len = current_len
                best_tour = improved_tour
                self.print_tour_to_stdout(best_tour)

        return best_tour

    def run(self):
        """Executes the full TSP solving pipeline."""
        start_time = time.time()
        self.deadline = start_time + self.time_limit - self.safety_margin

        self.read_problem_from_stdin()

        if self.num_cities == 1:
            self.print_tour_to_stdout([0])
            return

        self.neighbor_candidate_lists = self.build_candidate_neighbor_lists()

        # Step 1: construct an initial tour, print it immediately
        tour = self.construct_nearest_neighbor_tour(start_city=self.start_city)
        self.print_tour_to_stdout(tour)

        # Step 2: improve with neighbor-restricted 2-opt
        tour = self.optimize_tour_with_restricted_two_opt(tour)
        self.print_tour_to_stdout(tour)

        # Step 3: keep improving via random restarts / perturbation
        best_tour = self.run_iterated_local_search(tour)

        # Final guaranteed print, in case nothing above printed after some edit
        self.print_tour_to_stdout(best_tour)


if __name__ == "__main__":
    solver = TSPSolver()
    solver.run()
