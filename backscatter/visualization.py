"""Signal visualization helpers (matplotlib)."""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

# Vertical time markers drawn on A-scan plots: (time_s, color, label).
Vlines = list[tuple[float, str, str]]


def _draw_vlines(ax: plt.Axes, vlines: Vlines | None, legend: bool) -> None:
    """Draw vertical time markers; optionally attach their legend."""
    if not vlines:
        return
    for time_s, color, label in vlines:
        ax.axvline(time_s * 1e6, color=color, linewidth=1.3, alpha=0.85,
                   label=label)
    if legend:
        ax.legend(loc="lower right", fontsize=8, framealpha=0.9)


def plot_signals(
    t: np.ndarray,
    signals: list[tuple[str, np.ndarray]],
    title: str = "Signals",
    show: bool = True,
    save_path: str | Path | None = None,
    vlines: Vlines | None = None,
) -> np.ndarray:
    """Plot signals on stacked subplots with shared x and y limits.

    One subplot per signal, aligned vertically; the shared axes make
    amplitudes directly comparable between panels. Each panel carries
    a letter (а, б, в, ...) in its top-left corner, to be decoded in
    the figure caption of the document that embeds the plot.

    Args:
        t: Common time vector in seconds.
        signals: List of (label, samples) pairs, one panel each.
        title: Figure title.
        show: If True, display the figure immediately.
        save_path: If given, save the figure there (parent folders
            are created as needed).

    Returns:
        Array of the matplotlib Axes, one per signal.
    """
    fig, axes = plt.subplots(
        len(signals),
        1,
        sharex=True,
        sharey=True,
        figsize=(6.4, 2.0 * len(signals)),
    )
    for letter, ax, (label, signal) in zip("абвгдежи", axes, signals):
        ax.plot(t * 1e6, signal, linewidth=1.0)
        ax.set_ylabel("Amplitude")
        ax.grid(True)
        _draw_vlines(ax, vlines, legend=ax is axes[0])
        ax.text(
            0.01, 0.92, letter, transform=ax.transAxes,
            ha="left", va="top", fontsize=13, fontstyle="italic",
            bbox={"facecolor": "white", "edgecolor": "0.7", "pad": 3},
        )
        ax.text(
            0.99, 0.92, label, transform=ax.transAxes,
            ha="right", va="top",
            bbox={"facecolor": "white", "edgecolor": "0.7", "pad": 3},
        )
    axes[-1].set_xlabel("Time, µs")
    axes[0].set_title(title)
    fig.tight_layout()
    if save_path is not None:
        save_path = Path(save_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(save_path, dpi=150)
    if show:
        plt.show()
    return axes


def plot_depth_histogram(
    depths: np.ndarray,
    thickness: float | None = None,
    bins: int = 20,
    title: str = "Scatterer depth distribution",
    show: bool = True,
    save_path: str | Path | None = None,
) -> plt.Axes:
    """Plot a histogram of scatterer depths (count per depth bin).

    Args:
        depths: Scatterer depths in meters.
        thickness: Specimen thickness in meters; sets the histogram
            range and the expected-count line for a uniform
            distribution. Inferred from the data if omitted.
        bins: Number of depth bins.
        title: Plot title.
        show: If True, display the figure immediately.
        save_path: If given, save the figure there (parent folders
            are created as needed).

    Returns:
        The matplotlib Axes with the plot.
    """
    depths = np.asarray(depths, dtype=float)
    if thickness is None:
        thickness = float(depths.max())
    fig, ax = plt.subplots()
    ax.hist(
        depths * 1e3, bins=bins, range=(0.0, thickness * 1e3),
        edgecolor="white", linewidth=0.5,
    )
    ax.axhline(
        len(depths) / bins, color="0.3", linestyle="--", linewidth=1.2,
        label=f"uniform expectation: {len(depths) / bins:g} per bin",
    )
    ax.set_xlabel("Depth, mm")
    ax.set_ylabel("Number of scatterers")
    ax.set_title(title)
    ax.grid(True, axis="y")
    ax.legend()
    if save_path is not None:
        save_path = Path(save_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(save_path, dpi=150)
    if show:
        plt.show()
    return ax


def plot_signals_with_depth_histogram(
    t: np.ndarray,
    signals: list[tuple[str, np.ndarray]],
    depths: np.ndarray,
    velocity: float,
    time_offset: float = 0.0,
    thickness: float | None = None,
    bins: int = 20,
    title: str = "Signals and scatterer depths",
    show: bool = True,
    save_path: str | Path | None = None,
    vlines: Vlines | None = None,
) -> np.ndarray:
    """Plot A-scan panels with a depth histogram on the shared time axis.

    The bottom panel shows the scatterer count per depth bin, with
    each depth z unfolded to its echo arrival time t = t0 + 2 z / c.
    The bars therefore occupy exactly the interval between the
    entry-surface echo and the first backwall echo center, making the
    strict time-depth correspondence of the model explicit.

    Args:
        t: Common time vector in seconds.
        signals: List of (label, samples) pairs, one panel each.
        depths: Scatterer depths in meters.
        velocity: Longitudinal sound velocity c in m/s.
        time_offset: Transfer delay t0 in seconds (e.g. the prism
            round trip).
        thickness: Specimen thickness in meters; sets the histogram
            range. Inferred from the data if omitted.
        bins: Number of depth bins.
        title: Figure title.
        show: If True, display the figure immediately.
        save_path: If given, save the figure there (parent folders
            are created as needed).

    Returns:
        Array of the matplotlib Axes: signal panels, then histogram.
    """
    depths = np.asarray(depths, dtype=float)
    if thickness is None:
        thickness = float(depths.max())
    n_sig = len(signals)
    fig, axes = plt.subplots(
        n_sig + 1, 1, sharex=True, figsize=(6.4, 2.0 * (n_sig + 1))
    )
    letters = "абвгдежи"
    box = {"facecolor": "white", "edgecolor": "0.7", "pad": 3}
    y_max = 1.05 * max(np.max(np.abs(s)) for _, s in signals)
    for letter, ax, (label, signal) in zip(letters, axes[:-1], signals):
        ax.plot(t * 1e6, signal, linewidth=1.0)
        ax.set_ylim(-y_max, y_max)
        ax.set_ylabel("Amplitude")
        ax.grid(True)
        _draw_vlines(ax, vlines, legend=ax is axes[0])
        ax.text(0.01, 0.92, letter, transform=ax.transAxes, ha="left",
                va="top", fontsize=13, fontstyle="italic", bbox=box)
        ax.text(0.99, 0.92, label, transform=ax.transAxes, ha="right",
                va="top", bbox=box)
    ax = axes[-1]
    # Markers on the histogram panel too, without duplicate legend
    # entries (the panel keeps its own uniform-expectation legend).
    for time_s, color, _ in vlines or []:
        ax.axvline(time_s * 1e6, color=color, linewidth=1.3, alpha=0.85)
    times = (time_offset + 2 * depths / velocity) * 1e6
    span = (time_offset * 1e6, (time_offset + 2 * thickness / velocity) * 1e6)
    ax.hist(times, bins=bins, range=span, edgecolor="white", linewidth=0.5)
    ax.axhline(
        len(depths) / bins, color="0.3", linestyle="--", linewidth=1.2,
        label=f"uniform expectation: {len(depths) / bins:g} per bin",
    )
    ax.set_ylabel("Scatterers")
    ax.grid(True, axis="y")
    ax.text(0.01, 0.92, letters[n_sig], transform=ax.transAxes, ha="left",
            va="top", fontsize=13, fontstyle="italic", bbox=box)
    ax.legend(loc="upper right")
    axes[-1].set_xlabel("Time, µs")
    axes[0].set_title(title)
    fig.tight_layout()
    if save_path is not None:
        save_path = Path(save_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(save_path, dpi=150)
    if show:
        plt.show()
    return axes


def plot_attenuation_components(
    frequencies_mhz: np.ndarray,
    damping_coefficient: float,
    rayleigh_coefficient: float,
    marker_frequency: float | None = None,
    title: str = "Attenuation decomposition",
    show: bool = True,
    save_path: str | Path | None = None,
) -> plt.Axes:
    """Plot the Mason-McSkimin attenuation decomposition vs frequency.

    Draws the damping (absorption) component Cd*f, the Rayleigh
    scattering component CR*f^4 and their sum (README, section 7).

    Args:
        frequencies_mhz: Frequency grid in MHz.
        damping_coefficient: Cd in dB/m/MHz.
        rayleigh_coefficient: CR in dB/m/MHz^4.
        marker_frequency: Optional frequency (MHz) to mark with a
            vertical line (e.g. the carrier frequency).
        title: Plot title.
        show: If True, display the figure immediately.
        save_path: If given, save the figure there (parent folders
            are created as needed).

    Returns:
        The matplotlib Axes with the plot.
    """
    f = np.asarray(frequencies_mhz, dtype=float)
    damping = damping_coefficient * f
    scattering = rayleigh_coefficient * f**4
    fig, ax = plt.subplots()
    ax.plot(f, damping, label="damping (absorption): $C_d f$")
    ax.plot(f, scattering, label="Rayleigh scattering: $C_R f^4$")
    ax.plot(f, damping + scattering, "k--", linewidth=1.2, label="total")
    if marker_frequency is not None:
        ax.axvline(marker_frequency, color="0.4", linestyle=":",
                   linewidth=1.2)
        ax.text(marker_frequency, ax.get_ylim()[1] * 0.03,
                f" $f_0$ = {marker_frequency:g} MHz", ha="left", fontsize=9)
    ax.set_xlabel("Frequency, MHz")
    ax.set_ylabel("Attenuation, dB/m")
    ax.set_title(title)
    ax.grid(True)
    ax.legend()
    if save_path is not None:
        save_path = Path(save_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(save_path, dpi=150)
    if show:
        plt.show()
    return ax


def plot_signal(
    t: np.ndarray,
    signal: np.ndarray,
    title: str = "Signal",
    show: bool = True,
    save_path: str | Path | None = None,
    vlines: Vlines | None = None,
) -> plt.Axes:
    """Plot a time-domain signal with time in microseconds.

    Args:
        t: Time vector in seconds.
        signal: Signal samples.
        title: Plot title.
        show: If True, display the figure immediately.
        save_path: If given, save the figure there (parent folders
            are created as needed).
        vlines: Optional vertical time markers (time_s, color, label).

    Returns:
        The matplotlib Axes with the plot.
    """
    fig, ax = plt.subplots()
    ax.plot(t * 1e6, signal)
    ax.set_xlabel("Time, µs")
    ax.set_ylabel("Amplitude")
    ax.set_title(title)
    ax.grid(True)
    _draw_vlines(ax, vlines, legend=True)
    if save_path is not None:
        save_path = Path(save_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(save_path, dpi=150)
    if show:
        plt.show()
    return ax
