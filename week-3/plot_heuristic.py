import math

import matplotlib.pyplot as plt

from graph_data import graph


GOAL = "G"


def heuristic_euclidean(node_id: str) -> float:
    gx, gy = graph[GOAL].location
    x, y = graph[node_id].location
    return round(math.sqrt((x - gx) ** 2 + (y - gy) ** 2), 1)


def heuristic_manhattan(node_id: str) -> int:
    gx, gy = graph[GOAL].location
    x, y = graph[node_id].location
    return abs(x - gx) + abs(y - gy)


def plot_heuristic(heuristic_fn, title: str, filename: str):
    fig, ax = plt.subplots(figsize=(10, 7))

    drawn_edges = set()

    # Draw Edges
    for node_id, node in graph.items():
        x1, y1 = node.location

        for neighbor_id in node.neighbors:
            edge = tuple(sorted((node_id, neighbor_id)))

            if edge not in drawn_edges:
                x2, y2 = graph[neighbor_id].location
                ax.plot([x1, x2], [y1, y2], color="black", linewidth=1.5, zorder=1)
                drawn_edges.add(edge)

    # Draw Nodes with Heuristic Labels
    for node_id, node in graph.items():
        x, y = node.location
        h = heuristic_fn(node_id)

        is_special = node_id in ["S", "G"]
        color = "red" if is_special else "black"

        ax.scatter(
            x,
            y,
            s=500,
            facecolor="white",
            edgecolor=color,
            linewidth=2.5 if is_special else 1.5,
            zorder=4,
        )

        # Node label inside the circle
        ax.text(
            x,
            y,
            node_id,
            fontsize=12,
            fontweight="bold",
            color=color,
            ha="center",
            va="center",
            zorder=5,
        )

        # Heuristic value below the node circle
        ax.text(
            x,
            y - 0.55,
            f"h={h}",
            fontsize=9,
            color=color,
            ha="center",
            va="top",
            zorder=5,
        )

    # Axes, Grid and Ticks
    max_x = max(node.location[0] for node in graph.values()) + 1
    max_y = max(node.location[1] for node in graph.values()) + 1

    ax.set_xlim(-1, max_x)
    ax.set_ylim(-1, max_y)

    ax.set_xticks(range(max_x + 1))
    ax.set_yticks(range(max_y + 1))

    ax.tick_params(
        axis="both", which="major", direction="out", length=5, width=1, labelsize=10
    )

    ax.grid(True, linestyle="--", color="gray", alpha=0.5)

    for spine in ax.spines.values():
        spine.set_visible(True)
        spine.set_linewidth(1.2)
        spine.set_color("black")

    ax.set_aspect("equal")
    ax.set_title(title, fontsize=14, fontweight="bold", pad=12)

    plt.savefig(filename, dpi=300, bbox_inches="tight")
    plt.close(fig)


plot_heuristic(heuristic_euclidean, "Euclidean Heuristic", "plot_heuristic_euclidean.png")
plot_heuristic(heuristic_manhattan, "Manhattan Heuristic", "plot_heuristic_manhattan.png")
