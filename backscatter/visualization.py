"""Signal visualization helpers (matplotlib)."""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


def plot_signals(
    t: np.ndarray,
    signals: list[tuple[str, np.ndarray]],
    title: str = "Signals",
    show: bool = True,
    save_path: str | Path | None = None,
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


def plot_signal(
    t: np.ndarray,
    signal: np.ndarray,
    title: str = "Signal",
    show: bool = True,
    save_path: str | Path | None = None,
) -> plt.Axes:
    """Plot a time-domain signal with time in microseconds.

    Args:
        t: Time vector in seconds.
        signal: Signal samples.
        title: Plot title.
        show: If True, display the figure immediately.
        save_path: If given, save the figure there (parent folders
            are created as needed).

    Returns:
        The matplotlib Axes with the plot.
    """
    fig, ax = plt.subplots()
    ax.plot(t * 1e6, signal)
    ax.set_xlabel("Time, µs")
    ax.set_ylabel("Amplitude")
    ax.set_title(title)
    ax.grid(True)
    if save_path is not None:
        save_path = Path(save_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(save_path, dpi=150)
    if show:
        plt.show()
    return ax
