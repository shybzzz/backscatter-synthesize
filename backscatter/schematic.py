"""Schematic of the measurement setup (README, fig. 2).

Draws a cross-section of the plane-parallel specimen with the
dual-element transducer on its outer surface and the pulse propagation
path unfolded along the horizontal (time) axis: the transmitted pulse
travels to the inner (back) wall, returns to the outer surface where
it is recorded, is reflected back into the specimen, and so on. The
k-th echo arrives at t = k * tau (README, formula (3)) with the
amplitude decaying according to formula (4); the decay is suggested by
the thinning of the ray arrows. Labels are in Ukrainian to match the
README. The horizontal spread of the rays is a drawing convention for
normal incidence, not a real oblique path.
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Rectangle

# Layout constants (arbitrary drawing units): specimen occupies
# y in [-D, 0], the transducer sits above the outer surface y = 0.
WIDTH = 13.0
D = 3.0  # drawn specimen thickness
LEG = 1.6  # horizontal advance of one ray leg (half round trip)


def draw_schematic(
    save_path: str | Path | None = None,
    show: bool = True,
) -> plt.Axes:
    """Draw the setup schematic; optionally save it to `save_path`."""
    fig, ax = plt.subplots(figsize=(9, 5.5))

    # Specimen cross-section.
    ax.add_patch(
        Rectangle((0, -D), WIDTH, D, facecolor="0.88", edgecolor="black", hatch="..")
    )
    ax.text(
        WIDTH - 0.15,
        -D / 2,
        "сталевий зразок",
        ha="right",
        va="center",
        fontsize=11,
        bbox={"facecolor": "white", "edgecolor": "none", "pad": 2},
    )

    # Dual-element transducer: transmitter and receiver separated by
    # an acoustic barrier (vertical line between the elements).
    ax.add_patch(Rectangle((0.6, 0), 1.5, 0.9, facecolor="0.65", edgecolor="black"))
    ax.add_patch(Rectangle((2.2, 0), 1.5, 0.9, facecolor="0.65", edgecolor="black"))
    ax.plot([2.15, 2.15], [0, 1.15], color="black", linewidth=2)
    ax.text(1.35, 1.05, "випромінювач", ha="center", fontsize=10)
    ax.text(2.95, 1.35, "приймач", ha="center", fontsize=10)
    ax.text(2.15, 1.75, "роздільно-суміщений перетворювач", ha="center", fontsize=11)

    # Surface labels.
    ax.text(WIDTH - 0.15, 0.7, "зовнішня поверхня", ha="right", fontsize=10)
    ax.text(0.15, -D - 0.35, "внутрішня (донна) поверхня", ha="left", fontsize=10)

    # Thickness dimension arrow on the left.
    ax.annotate(
        "",
        xy=(-0.45, 0),
        xytext=(-0.45, -D),
        arrowprops={"arrowstyle": "<->", "color": "black"},
    )
    ax.text(-0.65, -D / 2, "$d$", ha="right", va="center", fontsize=13)

    # Propagation path unfolded to the right: each leg is one traversal
    # of the thickness; every second vertex at y = 0 is an echo arrival.
    # Line width decays with the leg number to suggest attenuation (4).
    x0 = 1.35  # start under the transmitting element
    n_legs = 7
    for leg in range(n_legs):
        x_a, x_b = x0 + leg * LEG, x0 + (leg + 1) * LEG
        y_a, y_b = (0, -D) if leg % 2 == 0 else (-D, 0)
        width = 2.4 * 0.82**leg
        ax.annotate(
            "",
            xy=(x_b, y_b),
            xytext=(x_a, y_a),
            arrowprops={"arrowstyle": "-|>", "color": "C0", "linewidth": width},
        )

    # Time axis under the specimen: the horizontal unfolding of the
    # ray path is temporal, not spatial — the wave itself travels only
    # along the thickness. Dashed guides drop from the registration
    # points at the outer surface to the axis ticks at t = k * tau.
    axis_y = -D - 1.5
    ax.annotate(
        "",
        xy=(WIDTH, axis_y),
        xytext=(0.7, axis_y),
        arrowprops={"arrowstyle": "-|>", "color": "black"},
    )
    ax.text(WIDTH + 0.15, axis_y, "$t$", ha="left", va="center", fontsize=13)
    tt = np.linspace(0, 1, 200)
    burst = np.exp(-0.5 * ((tt - 0.5) / (1 / 6)) ** 2) * np.sin(2 * np.pi * 7 * tt)
    for k in range((n_legs + 1) // 2 + 1):
        x_k = x0 + 2 * k * LEG
        if x_k > WIDTH - 0.3:
            break
        if k > 0:  # echo arrival at the outer surface
            ax.plot(x_k, 0, marker="o", color="C3", markersize=5, zorder=5)
            ax.plot(
                [x_k, x_k], [axis_y, 0], color="0.45", linewidth=0.8,
                linestyle="--", zorder=1,
            )
            # Recorded echo on the time axis, decaying with k as a
            # visual counterpart of formula (4).
            amp = 0.5 * 0.75 ** (k - 1)
            ax.plot(
                x_k - 0.45 + 0.9 * tt, axis_y + amp * burst,
                color="C0", linewidth=1.1, zorder=3,
            )
        label = "$0$" if k == 0 else rf"${k}\tau$" if k > 1 else r"$\tau$"
        ax.plot([x_k, x_k], [axis_y - 0.08, axis_y + 0.08], color="black")
        ax.text(x_k, axis_y - 0.7, label, ha="center", va="top", fontsize=12)

    # A small copy of the excitation pulse beside the first leg
    # (`tt`/`burst` are defined with the time axis above).
    ax.plot(0.75 + 0.5 * tt, -1.9 + 0.55 * burst, color="C0", linewidth=1)
    ax.text(
        1.0,
        -1.15,
        "зондувальний\nімпульс",
        ha="center",
        fontsize=9,
        color="C0",
        bbox={"facecolor": "white", "edgecolor": "none", "pad": 2},
    )

    ax.set_xlim(-1.4, WIDTH + 0.6)
    ax.set_ylim(-D - 2.9, 2.1)
    ax.set_aspect("equal")
    ax.axis("off")
    fig.tight_layout()

    if save_path is not None:
        save_path = Path(save_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(save_path, dpi=150)
    if show:
        plt.show()
    return ax
