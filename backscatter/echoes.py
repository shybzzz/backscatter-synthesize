"""Generic periodic echo train from a reverberating cavity.

A pulse reverberates between two parallel boundaries a distance z
apart in a medium with sound velocity c and attenuation alpha: one
boundary is a perfect reflector (|R| ~ 1), the other a partial
reflector with amplitude reflection coefficient r. Echo number k
completes k round trips and arrives at

    t_k = t_0 + k * tau,   tau = 2 z / c,

with amplitude

    A_k = S * r**k * 10 ** (-alpha * 2 z k / 20),

where alpha is in dB/m at the carrier frequency. The factors S
(`scale`) and t_0 (`time_offset`) describe the transfer path between
the transducer and the cavity: for a cavity observed directly at the
surface S = 1, t_0 = 0; for one observed through an intermediate
layer (e.g. a delay-line prism) S collects the transmission and
attenuation losses of that layer and t_0 its propagation delay.

Two optional hooks generalize the train to oblique (pitch-catch)
geometries, where the echo of the k-th round trip is the echo of a
reflector at the UNFOLDED one-way depth z_k = k z (mirror-image
method):

- `sensitivity(z_k)` — an extra amplitude factor depending on the
  unfolded depth, e.g. the depth sensitivity D(z) of a dual-element
  probe whose transmit and receive beams cross under the surface
  (README, section 8);
- `path_length(z_k)` — the two-way sound path in the medium for that
  unfolded depth; the default 2 z_k is the normal-incidence path, a
  dual-element probe gives the V-path 2 sqrt(z_k**2 + a**2). It sets
  both the arrival time (path / c) and the attenuation
  (10**(-alpha * path / 20)).

With both hooks the k-th echo is

    A_k = S * r**k * D(k z) * 10 ** (-alpha * L(k z) / 20),
    t_k = t_0 + L(k z) / c.

Used by backscatter.specimen (backwall echoes, z = specimen
thickness, r = 1), backscatter.transducer (prism reverberation and
the specimen train seen through the prism) and
backscatter.dual_element (the same families seen by a dual-element
probe).
"""

from collections.abc import Callable

import numpy as np

from backscatter.pulse import DEFAULT_SAMPLE_RATE

DEFAULT_N_SAMPLES = 1400

# An echo below this fraction of the transmitted amplitude (-80 dB)
# is considered fully attenuated and the train is terminated.
ECHO_AMPLITUDE_FLOOR = 1e-4

# Hooks of the oblique-geometry generalization: amplitude factor and
# two-way sound path as functions of the unfolded one-way depth (m).
DepthFunction = Callable[[float], float]


def normal_path_length(depth: float) -> float:
    """Two-way sound path at normal incidence: 2 z (the default hook)."""
    return 2.0 * depth


def add_scatterer_echoes(
    pulse: np.ndarray,
    depth: float,
    velocity: float,
    attenuation: float,
    sample_rate: float = DEFAULT_SAMPLE_RATE,
    reflectivity: float = 1.0,
    scale: float = 1.0,
    time_offset: float = 0.0,
    sensitivity: DepthFunction | None = None,
    path_length: DepthFunction | None = None,
    n_samples: int = DEFAULT_N_SAMPLES,
    signal: np.ndarray | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """Add the periodic echo train of a reflector at `depth` to a signal.

    Args:
        pulse: Excitation pulse samples (already at `sample_rate`).
        depth: Reflector depth z below the reverberation entry
            surface, in meters.
        velocity: Longitudinal sound velocity c in m/s of the medium
            between the surface and the reflector.
        attenuation: Attenuation coefficient alpha in dB/m at the
            carrier frequency.
        sample_rate: Sampling rate in Hz.
        reflectivity: Amplitude reflection coefficient r of the
            reflector; 1 corresponds to a perfectly reflecting
            boundary such as a backwall.
        scale: Extra amplitude factor S applied to every echo
            (transfer losses outside the reverberation cavity).
        time_offset: Extra delay t_0 in seconds added to every echo
            (transfer delay outside the reverberation cavity).
        sensitivity: Optional amplitude factor D(z_k) of the echo as
            a function of its unfolded one-way depth z_k = k * depth
            (e.g. the depth sensitivity of a dual-element probe);
            None means 1 for every echo.
        path_length: Optional two-way sound path L(z_k) in the medium
            as a function of the unfolded one-way depth; None means
            the normal-incidence path 2 z_k. Determines both the
            arrival time L/c and the attenuation along L.
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
    if path_length is None:
        path_length = normal_path_length

    for k in range(1, n_samples):
        unfolded_depth = k * depth
        path = path_length(unfolded_depth)
        amplitude = (
            scale * reflectivity**k * 10 ** (-attenuation * path / 20)
        )
        if sensitivity is not None:
            amplitude *= sensitivity(unfolded_depth)
        if abs(amplitude) < ECHO_AMPLITUDE_FLOOR:
            break
        start = round((time_offset + path / velocity) * sample_rate)
        if start >= n_samples:
            break
        stop = min(start + len(pulse), n_samples)
        signal[start:stop] += amplitude * pulse[: stop - start]
    return t, signal
