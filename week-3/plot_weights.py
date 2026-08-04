import matplotlib.pyplot as plt

from graph_data import graph, edge_weights


# -----------------------------
# Create Figure
# -----------------------------
fig, ax = plt.subplots(figsize=(10, 7))

drawn_edges = set()


# -----------------------------
# Draw Edges & Weights
# -----------------------------
for node_id, node in graph.items():
    x1, y1 = node.location

    for neighbor_id in node.neighbors:
        edge = tuple(sorted((node_id, neighbor_id)))

        if edge not in drawn_edges:
            x2, y2 = graph[neighbor_id].location

            # Edge
            ax.plot([x1, x2], [y1, y2], color="black", linewidth=1.5, zorder=1)

            # Weight at midpoint
            mx = (x1 + x2) / 2
            my = (y1 + y2) / 2

            ax.text(
                mx,
                my,
                str(edge_weights[edge]),
                fontsize=11,
                ha="center",
                va="center",
                bbox=dict(facecolor="white", edgecolor="none", alpha=0.9, pad=0.15),
                zorder=3,
            )

            drawn_edges.add(edge)


# -----------------------------
# Draw Nodes
# -----------------------------
for node_id, node in graph.items():
    x, y = node.location

    is_special = node_id in ["S", "G"]

    ax.scatter(
        x,
        y,
        s=500,
        facecolor="white",
        edgecolor="red" if is_special else "black",
        linewidth=2.5 if is_special else 1.5,
        zorder=4,
    )

    ax.text(
        x,
        y,
        node_id,
        fontsize=12,
        fontweight="bold",
        color="red" if is_special else "black",
        ha="center",
        va="center",
        zorder=5,
    )


# -----------------------------
# Axes, Grid and Ticks
# -----------------------------
max_x = max(node.location[0] for node in graph.values()) + 1
max_y = max(node.location[1] for node in graph.values()) + 1

ax.set_xlim(-1, max_x)
ax.set_ylim(-1, max_y)

ax.set_xticks(range(max_x + 1))
ax.set_yticks(range(max_y + 1))

# Show axis numbers and tick marks
ax.tick_params(
    axis="both", which="major", direction="out", length=5, width=1, labelsize=10
)

# Draw grid
ax.grid(True, linestyle="--", color="gray", alpha=0.5)

# Draw the axis border (spines)
for spine in ax.spines.values():
    spine.set_visible(True)
    spine.set_linewidth(1.2)
    spine.set_color("black")

ax.set_aspect("equal")

# -----------------------------
# Save Figure
# -----------------------------
plt.savefig("plot_weights.png", dpi=300, bbox_inches="tight")
plt.close(fig)
