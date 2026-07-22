"""Excitation pulse generation."""

import numpy as np

DEFAULT_FREQUENCY = 10e6  # Hz
DEFAULT_SAMPLE_RATE = 68e6  # Hz
DEFAULT_N_PERIODS = 7


def generate_pulse(
    frequency: float = DEFAULT_FREQUENCY,
    sample_rate: float = DEFAULT_SAMPLE_RATE,
    n_periods: float = DEFAULT_N_PERIODS,
) -> tuple[np.ndarray, np.ndarray]:
    """Generate a single Gaussian-enveloped sinusoidal pulse.

    Args:
        frequency: Carrier frequency in Hz.
        sample_rate: Sampling rate in Hz.
        n_periods: Pulse duration expressed in carrier periods.

    Returns:
        (t, pulse): time vector in seconds and the pulse samples,
        both of the same length.
    """
    duration = n_periods / frequency
    t = np.arange(0, duration, 1 / sample_rate)

    # Gaussian envelope centered in the window; +/-3 sigma spans the
    # full duration so the pulse decays close to zero at the edges.
    center = duration / 2
    sigma = duration / 6
    envelope = np.exp(-0.5 * ((t - center) / sigma) ** 2)

    return t, envelope * np.sin(2 * np.pi * frequency * t)
