"""Schematics of the measurement setup (README, figs. 2 and 4).

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


def draw_prism_schematic(
    save_path: str | Path | None = None,
    show: bool = True,
) -> plt.Axes:
    """Draw the delay-line (prism) setup schematic (README, fig. 4).

    Same unfolded-time convention as `draw_schematic`: the horizontal
    axis is time, the vertical axis is depth. Horizontal advance is
    proportional to the actual travel time, so the ray slopes differ
    between the prism and the steel (different sound velocities), and
    the near-coincidence of the second backwall echo (t2 ~ 14.1 us)
    with the second interface echo (2 tau_p ~ 14.7 us) appears
    naturally. Ray widths decay according to the amplitude laws
    (README, formulas (7), (8)); the small pulses on the time axis are
    scaled to the actual relative amplitudes of the default model.
    """
    fig, ax = plt.subplots(figsize=(10, 6))
    scale = 0.6  # drawing units per microsecond
    H, D = 2.0, 2.5  # drawn prism and specimen thicknesses
    x_p = scale * 3.663  # one-way prism travel, 10 mm PMMA at 2730 m/s
    x_s = scale * 1.689  # one-way steel travel, 10 mm steel at 5920 m/s
    width = 12.6

    # Material layers: prism on top of the steel specimen.
    ax.add_patch(
        Rectangle((-0.9, -H), width + 0.9, H, facecolor="0.95",
                  edgecolor="black", hatch="//")
    )
    ax.add_patch(
        Rectangle((-0.9, -H - D), width + 0.9, D, facecolor="0.88",
                  edgecolor="black", hatch="..")
    )
    label_style = {"ha": "right", "va": "center", "fontsize": 10,
                   "bbox": {"facecolor": "white", "edgecolor": "none", "pad": 2}}
    ax.text(width - 0.2, -H / 2, "призма (оргскло)", **label_style)
    ax.text(width - 0.2, -H - 0.4, "межа оргскло–сталь", **label_style)
    ax.text(width - 0.2, -H - D / 2 - 0.45, "сталевий зразок", **label_style)
    ax.text(width - 0.2, -H - D - 0.35, "донна поверхня", ha="right",
            va="top", fontsize=10)

    # Piezo element glued to the top face of the prism.
    ax.add_patch(Rectangle((-0.6, 0), 1.2, 0.45, facecolor="0.65",
                           edgecolor="black"))
    ax.text(0, 0.7, "п'єзоелемент", ha="center", fontsize=10)

    # Thickness dimensions.
    for y0, y1, name in ((0, -H, "$h$"), (-H, -H - D, "$d$")):
        ax.annotate("", xy=(-1.15, y0), xytext=(-1.15, y1),
                    arrowprops={"arrowstyle": "<->", "color": "black"})
        ax.text(-1.35, (y0 + y1) / 2, name, ha="right", va="center",
                fontsize=13)

    def ray(p0, p1, color, lw):
        ax.annotate("", xy=p1, xytext=p0,
                    arrowprops={"arrowstyle": "-|>", "color": color,
                                "linewidth": lw})

    # Family 1 (README, formula (7)): reverberation inside the prism.
    ray((0, 0), (x_p, -H), "C0", 2.2)
    ray((x_p, -H), (2 * x_p, 0), "C0", 1.5)
    ray((2 * x_p, 0), (3 * x_p, -H), "C0", 0.9)
    ray((3 * x_p, -H), (4 * x_p, 0), "C0", 0.6)
    ax.text(2.7, -0.55, "реверберація в призмі", color="C0", fontsize=9,
            ha="center",
            bbox={"facecolor": "white", "edgecolor": "none", "pad": 2})

    # Family 2 (README, formula (8)): backwall train seen through the
    # prism. Zigzag in the steel; a prism leg branches off toward the
    # piezo at every interface touch.
    x = x_p
    widths = (1.8, 1.4, 0.9, 0.55)
    for k in range(3):
        ray((x, -H), (x + x_s, -H - D), "C2", widths[k])
        ray((x + x_s, -H - D), (x + 2 * x_s, -H), "C2", widths[k])
        ray((x + 2 * x_s, -H), (x + 2 * x_s + x_p, 0), "C2", widths[k + 1])
        x += 2 * x_s
    ax.text(2.3, -H - D - 0.5, "донна серія крізь призму", color="C2",
            fontsize=9, ha="center", va="top",
            bbox={"facecolor": "white", "edgecolor": "none", "pad": 2})

    # Time axis with registration marks and received pulses. Arrivals
    # and amplitudes follow the default model of README, section 3.
    axis_y = -H - D - 1.4
    ax.annotate("", xy=(width + 0.4, axis_y), xytext=(-0.4, axis_y),
                arrowprops={"arrowstyle": "-|>", "color": "black"})
    ax.text(width + 0.55, axis_y, "$t$", ha="left", va="center", fontsize=13)
    tt = np.linspace(0, 1, 200)
    burst = np.exp(-0.5 * ((tt - 0.5) / (1 / 6)) ** 2) * np.sin(2 * np.pi * 7 * tt)
    arrivals = (  # (x, tick label, stagger, pulse amplitude, family color)
        (0.0, "0", 0, None, None),
        (2 * x_p, "τп", 0, 0.31, "C0"),
        (x_p + 2 * x_s + x_p, "t₁", 0, 0.53, "C2"),
        (x_p + 4 * x_s + x_p, "t₂", 0, 0.20, "C2"),
        (4 * x_p, "2τп", 1, 0.04, "C0"),
        (x_p + 6 * x_s + x_p, "t₃", 0, 0.08, "C2"),
    )
    for x_k, label, stagger, amp, color in arrivals:
        ax.plot([x_k, x_k], [axis_y - 0.08, axis_y + 0.08], color="black")
        ax.text(x_k, axis_y - 0.3 - 0.5 * stagger, label, ha="center",
                va="top", fontsize=11)
        if amp is None:
            continue
        ax.plot(x_k, 0, marker="o", color="C3", markersize=5, zorder=5)
        ax.plot([x_k, x_k], [axis_y, 0], color="0.45", linewidth=0.8,
                linestyle="--", zorder=1)
        ax.plot(x_k - 0.35 + 0.7 * tt, axis_y + amp * burst, color=color,
                linewidth=1.1, zorder=3)

    ax.set_xlim(-1.7, width + 1.0)
    ax.set_ylim(axis_y - 1.3, 1.3)
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


def draw_flaw_schematic(
    save_path: str | Path | None = None,
    show: bool = True,
) -> plt.Axes:
    """Draw the flawed-specimen schematic (README, fig. 7).

    Same unfolded-time convention as `draw_prism_schematic`, with a
    plane flaw at depth z_f = 3 mm (dashed line) and three echo
    families in distinct colors: prism reverberation (C0), the
    interface-flaw train (C1) and the backwall train crossing the
    flaw (C2). With z_f = 0.3 d the flaw train (period 2 z_f / c) and
    the backwall train (period 2 d / c) stay separated on the time
    axis. Axis pulse amplitudes follow the default model of
    section 5.
    """
    fig, ax = plt.subplots(figsize=(10, 6))
    scale = 0.6  # drawing units per microsecond
    H, D = 2.0, 2.5  # drawn prism and specimen thicknesses
    x_p = scale * 3.663  # one-way prism travel
    x_f = scale * 0.507  # one-way steel travel to the flaw (3 mm)
    x_s = scale * 1.689  # one-way steel travel to the backwall (10 mm)
    y_f = -H - 0.3 * D  # drawn flaw depth (z_f = 0.3 d)
    width = 12.6

    # Material layers and the flaw line.
    ax.add_patch(
        Rectangle((-0.9, -H), width + 0.9, H, facecolor="0.95",
                  edgecolor="black", hatch="//")
    )
    ax.add_patch(
        Rectangle((-0.9, -H - D), width + 0.9, D, facecolor="0.88",
                  edgecolor="black", hatch="..")
    )
    ax.plot([-0.9, width], [y_f, y_f], color="firebrick", linewidth=1.8,
            linestyle=(0, (6, 3)), zorder=2)
    ax.text(0.4, y_f + 0.12, "дефект ($z_f$, $R_f$)", color="firebrick",
            fontsize=10, ha="left", va="bottom",
            bbox={"facecolor": "white", "edgecolor": "none", "pad": 2})
    label_style = {"ha": "right", "va": "center", "fontsize": 10,
                   "bbox": {"facecolor": "white", "edgecolor": "none", "pad": 2}}
    ax.text(width - 0.2, -H / 2, "призма (оргскло)", **label_style)
    ax.text(width - 0.2, -H - 0.35, "межа оргскло–сталь", **label_style)
    ax.text(width - 0.2, -H - D + 0.35, "сталевий зразок", **label_style)
    ax.text(width - 0.2, -H - D - 0.35, "донна поверхня", ha="right",
            va="top", fontsize=10)

    # Piezo element and thickness dimensions.
    ax.add_patch(Rectangle((-0.6, 0), 1.2, 0.45, facecolor="0.65",
                           edgecolor="black"))
    ax.text(0, 0.7, "п'єзоелемент", ha="center", fontsize=10)
    for y0, y1, name in ((0, -H, "$h$"), (-H, y_f, "$z_f$"),
                         (-H, -H - D, "$d$")):
        x_dim = -1.15 if name != "$z_f$" else -0.55
        ax.annotate("", xy=(x_dim, y0), xytext=(x_dim, y1),
                    arrowprops={"arrowstyle": "<->", "color": "black"})
        ax.text(x_dim - 0.2, (y0 + y1) / 2, name, ha="right", va="center",
                fontsize=12)

    def ray(p0, p1, color, lw):
        ax.annotate("", xy=p1, xytext=p0,
                    arrowprops={"arrowstyle": "-|>", "color": color,
                                "linewidth": lw})

    # Family 1: prism reverberation (C0).
    ray((0, 0), (x_p, -H), "C0", 2.2)
    ray((x_p, -H), (2 * x_p, 0), "C0", 1.4)
    ray((2 * x_p, 0), (3 * x_p, -H), "C0", 0.8)
    ray((3 * x_p, -H), (4 * x_p, 0), "C0", 0.55)

    # Family 3 first (wider, drawn beneath family 2 where legs
    # coincide): backwall train crossing the flaw (C2).
    x = x_p
    for k in range(2):
        w = (1.6, 1.0)[k]
        ray((x, -H), (x + x_s, -H - D), "C2", w)
        ray((x + x_s, -H - D), (x + 2 * x_s, -H), "C2", w)
        ray((x + 2 * x_s, -H), (x + 2 * x_s + x_p, 0), "C2", w)
        x += 2 * x_s

    # Family 2: reverberation between the interface and the flaw (C1).
    x = x_p
    for k in range(2):
        w = (1.3, 0.8)[k]
        ray((x, -H), (x + x_f, y_f), "C1", w)
        ray((x + x_f, y_f), (x + 2 * x_f, -H), "C1", w)
        ray((x + 2 * x_f, -H), (x + 2 * x_f + x_p, 0), "C1", w * 0.7)
        x += 2 * x_f

    # Colour key (top right, above the prism).
    for i, (color, label) in enumerate((
        ("C0", "реверберація в призмі"),
        ("C1", "відбиття від дефекту"),
        ("C2", "донна серія крізь дефект"),
    )):
        y_key = 1.45 - 0.42 * i
        ax.plot([7.4, 8.0], [y_key, y_key], color=color, linewidth=2)
        ax.text(8.15, y_key, label, ha="left", va="center", fontsize=9)

    # Time axis, registration marks and received pulses (README,
    # section 5 amplitudes, x3 for visibility).
    axis_y = -H - D - 1.4
    ax.annotate("", xy=(width + 0.4, axis_y), xytext=(-0.4, axis_y),
                arrowprops={"arrowstyle": "-|>", "color": "black"})
    ax.text(width + 0.55, axis_y, "$t$", ha="left", va="center", fontsize=13)
    tt = np.linspace(0, 1, 200)
    burst = np.exp(-0.5 * ((tt - 0.5) / (1 / 6)) ** 2) * np.sin(2 * np.pi * 7 * tt)
    arrivals = (  # (x, label, stagger, [(amplitude, colour), ...])
        (0.0, "0", 0, ()),
        (2 * x_p, "τп", 0, ((0.61, "C0"),)),
        (x_p + 2 * x_f + x_p, "f₁", 0, ((0.086, "C1"),)),
        (x_p + 4 * x_f + x_p, "f₂", 1, ((0.048, "C1"),)),
        (x_p + 2 * x_s + x_p, "d₁", 0, ((0.079, "C2"),)),
        (x_p + 4 * x_s + x_p, "d₂", 0, ((0.04, "C2"),)),
        (4 * x_p, "2τп", 1, ((0.126, "C0"),)),
    )
    for x_k, label, stagger, pulses in arrivals:
        ax.plot([x_k, x_k], [axis_y - 0.08, axis_y + 0.08], color="black")
        ax.text(x_k, axis_y - 0.75 - 0.5 * stagger, label, ha="center",
                va="top", fontsize=11)
        if not pulses:
            continue
        ax.plot(x_k, 0, marker="o", color="C3", markersize=5, zorder=5)
        ax.plot([x_k, x_k], [axis_y, 0], color="0.45", linewidth=0.8,
                linestyle="--", zorder=1)
        for amp, color in pulses:
            ax.plot(x_k - 0.35 + 0.7 * tt, axis_y + amp * burst,
                    color=color, linewidth=1.1, zorder=3)

    ax.set_xlim(-1.9, width + 1.0)
    ax.set_ylim(axis_y - 1.9, 1.8)
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
