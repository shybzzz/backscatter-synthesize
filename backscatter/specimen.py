"""Plane-parallel specimen model: periodic backwall echo train.

The transducer rests on the outer surface of a plane-parallel steel
specimen of thickness d. The transmitted pulse travels to the inner
(back) wall, reflects, returns to the outer surface where it is
recorded, reflects there again into the specimen, and the cycle
repeats until the pulse has fully attenuated. Echo number k therefore
completes k round trips and arrives at

    t_k = k * tau,   tau = 2 d / c,

where c is the longitudinal sound velocity. Its amplitude is reduced
by material attenuation accumulated over the traveled path 2 d k:

    A_k = 10 ** (-alpha * 2 d k / 20),

with alpha the attenuation coefficient in dB/m at the carrier
frequency. Working assumptions of this stage (see README, section 2):

- both boundaries are perfect reflectors (steel-air interface,
  |R| ~ 1), so reflection losses are neglected;
- attenuation is a scalar at the carrier frequency; its frequency
  dependence within the pulse band is deferred to a later stage;
- echo arrival times are rounded to the nearest sample, i.e. a
  residual sub-sample delay below T_s/2 is neglected;
- beam spreading (diffraction) losses are not modelled.
"""

import numpy as np

from backscatter.pulse import DEFAULT_SAMPLE_RATE

DEFAULT_THICKNESS = 10e-3  # m
DEFAULT_VELOCITY = 5920.0  # m/s, longitudinal wave in steel
DEFAULT_ATTENUATION = 20.0  # dB/m at the carrier frequency
DEFAULT_N_SAMPLES = 1400

# An echo below this fraction of the transmitted amplitude (-80 dB)
# is considered fully attenuated and the train is terminated.
ECHO_AMPLITUDE_FLOOR = 1e-4


def add_backwall_echoes(
    pulse: np.ndarray,
    sample_rate: float = DEFAULT_SAMPLE_RATE,
    thickness: float = DEFAULT_THICKNESS,
    velocity: float = DEFAULT_VELOCITY,
    attenuation: float = DEFAULT_ATTENUATION,
    n_samples: int = DEFAULT_N_SAMPLES,
    signal: np.ndarray | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """Add the periodic backwall echo train of a pulse to a signal.

    Args:
        pulse: Excitation pulse samples (already at `sample_rate`).
        sample_rate: Sampling rate in Hz.
        thickness: Specimen thickness d in meters.
        velocity: Longitudinal sound velocity c in m/s.
        attenuation: Attenuation coefficient alpha in dB/m at the
            carrier frequency.
        n_samples: Length of the result signal; ignored if `signal`
            is given.
        signal: Optional existing signal to add the echoes to; it is
            not modified, a copy is returned.

    Returns:
        (t, signal): time vector in seconds and the signal with the
        echo train added, both of length `n_samples`.
    """
    if signal is None:
        signal = np.zeros(n_samples)
    else:
        signal = np.asarray(signal, dtype=float).copy()
        n_samples = len(signal)
    t = np.arange(n_samples) / sample_rate

    round_trip = 2 * thickness / velocity
    for k in range(1, n_samples):
        amplitude = 10 ** (-attenuation * 2 * thickness * k / 20)
        if amplitude < ECHO_AMPLITUDE_FLOOR:
            break
        start = round(k * round_trip * sample_rate)
        if start >= n_samples:
            break
        stop = min(start + len(pulse), n_samples)
        signal[start:stop] += amplitude * pulse[: stop - start]
    return t, signal
