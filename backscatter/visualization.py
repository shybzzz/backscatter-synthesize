"""Signal visualization helpers (matplotlib)."""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


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
