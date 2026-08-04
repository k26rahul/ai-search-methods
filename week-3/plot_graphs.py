import math

import matplotlib.pyplot as plt

from graph_data import graph, edge_weights


GOAL = "G"


def heuristic_manhattan(node_id: str) -> int:
    gx, gy = graph[GOAL].location
    x, y = graph[node_id].location
    return abs(x - gx) + abs(y - gy)


def euclidean_distance(node_a: str, node_b: str) -> float:
    x1, y1 = graph[node_a].location
    x2, y2 = graph[node_b].location
    return round(math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2), 1)


def setup_axes(ax, title: str):
    """Configure axes, grid, spines, and title."""
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


def draw_edges(ax):
    drawn_edges = set()
    for node_id, node in graph.items():
        x1, y1 = node.location
        for neighbor_id in node.neighbors:
            edge = tuple(sorted((node_id, neighbor_id)))
            if edge not in drawn_edges:
                x2, y2 = graph[neighbor_id].location
                ax.plot([x1, x2], [y1, y2], color="black", linewidth=1.5, zorder=1)
                drawn_edges.add(edge)


def draw_nodes(ax, show_heuristic=False):
    for node_id, node in graph.items():
        x, y = node.location

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

        if show_heuristic:
            h = heuristic_manhattan(node_id)
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


def draw_edge_labels(ax, label_fn):
    """Draw labels on edges using the provided label function."""
    drawn_edges = set()
    for node_id, node in graph.items():
        for neighbor_id in node.neighbors:
            edge = tuple(sorted((node_id, neighbor_id)))
            if edge not in drawn_edges:
                x1, y1 = graph[node_id].location
                x2, y2 = graph[neighbor_id].location
                mx, my = (x1 + x2) / 2, (y1 + y2) / 2
                label = label_fn(edge, node_id, neighbor_id)
                ax.text(
                    mx,
                    my,
                    str(label),
                    fontsize=9,
                    color="blue",
                    fontweight="bold",
                    ha="center",
                    va="center",
                    bbox=dict(facecolor="white", edgecolor="none", alpha=0.9, pad=1),
                    zorder=3,
                )
                drawn_edges.add(edge)


def save_plot(ax, fig, filename: str):
    plt.savefig(filename, dpi=300, bbox_inches="tight")
    plt.close(fig)


# Plot 1: Manhattan heuristic values on each node
fig, ax = plt.subplots(figsize=(10, 7))
draw_edges(ax)
draw_nodes(ax, show_heuristic=True)
setup_axes(ax, "Manhattan Heuristic (h values)")
save_plot(ax, fig, "plot_manhattan_heuristic.png")

# Plot 2: Euclidean distance as edge costs
fig, ax = plt.subplots(figsize=(10, 7))
draw_edges(ax)
draw_edge_labels(ax, lambda edge, a, b: euclidean_distance(a, b))
draw_nodes(ax)
setup_axes(ax, "Edge Costs (Euclidean Distance)")
save_plot(ax, fig, "plot_euclidean_edge_costs.png")

# Plot 3: Given edge weights from graph data
fig, ax = plt.subplots(figsize=(10, 7))
draw_edges(ax)
draw_edge_labels(ax, lambda edge, a, b: edge_weights[edge])
draw_nodes(ax)
setup_axes(ax, "Edge Weights (Given)")
save_plot(ax, fig, "plot_given_edge_weights.png")
