"""Excitation pulse generation via scipy.signal.gausspulse.

Alternative to backscatter.pulse.generate_pulse that delegates the
waveform synthesis to the library routine. Both produce the same
signal (README, formula (1)); this module exists to demonstrate the
equivalence and to cross-check the hand-written implementation.

Three adaptations are required, because gausspulse is parameterized
differently from our model:

1. Envelope width: gausspulse defines the Gaussian by its fractional
   spectral bandwidth `bw` at the reference level `bwr` (dB), i.e. its
   envelope is exp(-a t^2) with

       a = -(pi f0 bw)^2 / (4 ln r),   r = 10^(bwr/20),

   whereas our model defines it in the time domain as
   exp(-t^2 / (2 sigma^2)) with sigma = T/6 (formula (2)).
   Equating the two exponents gives the conversion

       bw = sqrt(-2 ln r) / (pi f0 sigma).

2. Time origin: gausspulse centers the envelope at t = 0 and has
   infinite support; our pulse lives on the window [0, T] with the
   envelope centered at t_c = T/2. Hence the routine is evaluated at
   the shifted argument t - t_c, which also truncates the tails.

3. Carrier phase: gausspulse uses a cosine carrier referenced to the
   envelope center, cos(2 pi f0 (t - t_c)), while formula (1) uses a
   sine referenced to the window start, sin(2 pi f0 t). With the
   quadrature pair (yI, yQ) = env * (cos x, sin x), x = 2 pi f0 (t - t_c),
   the angle-sum identity restores the required carrier:

       sin(2 pi f0 t) * env = yQ cos(phi) + yI sin(phi),
       phi = 2 pi f0 t_c.
"""

import numpy as np
from scipy.signal import gausspulse

from backscatter.pulse import (
    DEFAULT_FREQUENCY,
    DEFAULT_N_PERIODS,
    DEFAULT_SAMPLE_RATE,
)

# Reference level (dB) at which gausspulse measures the fractional
# bandwidth; -6 dB is the conventional level for transducer specs.
BANDWIDTH_REF_DB = -6


def generate_pulse_scipy(
    frequency: float = DEFAULT_FREQUENCY,
    sample_rate: float = DEFAULT_SAMPLE_RATE,
    n_periods: float = DEFAULT_N_PERIODS,
) -> tuple[np.ndarray, np.ndarray]:
    """Generate the Gaussian-enveloped pulse using scipy.signal.gausspulse.

    Same signature and result as backscatter.pulse.generate_pulse.

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
    center = duration / 2
    sigma = duration / 6

    # Adaptation 1: duration-in-periods -> fractional bandwidth.
    ref = 10 ** (BANDWIDTH_REF_DB / 20)
    bandwidth = np.sqrt(-2 * np.log(ref)) / (np.pi * frequency * sigma)

    # Adaptation 2: evaluate at t - t_c to center the envelope in the
    # window; adaptation 3: take the quadrature pair to rebuild the
    # sine carrier referenced to the window start.
    in_phase, quadrature = gausspulse(
        t - center,
        fc=frequency,
        bw=bandwidth,
        bwr=BANDWIDTH_REF_DB,
        retquad=True,
    )
    phi = 2 * np.pi * frequency * center
    return t, quadrature * np.cos(phi) + in_phase * np.sin(phi)
