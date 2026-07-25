"""Steel specimen model: backwall echo train.

The plane-parallel steel specimen of thickness d is probed from its
outer surface; the inner (back) wall is a steel-air interface and thus
a practically perfect reflector (|R| ~ 1). The backwall echo train is
the particular case of the generic reverberation train
(backscatter.echoes.add_scatterer_echoes) with depth z = d and
reflectivity r = 1: echoes arrive at t_k = k * 2d/c with amplitudes
10 ** (-alpha * 2dk / 20) (README, section 2, formulas (3), (4)).
"""

import numpy as np

from backscatter.echoes import DEFAULT_N_SAMPLES, add_scatterer_echoes
from backscatter.pulse import DEFAULT_SAMPLE_RATE

DEFAULT_THICKNESS = 10e-3  # m
DEFAULT_VELOCITY = 5920.0  # m/s, longitudinal wave in steel
DEFAULT_ATTENUATION = 20.0  # dB/m at the carrier frequency


def add_backwall_echoes(
    pulse: np.ndarray,
    sample_rate: float = DEFAULT_SAMPLE_RATE,
    thickness: float = DEFAULT_THICKNESS,
    velocity: float = DEFAULT_VELOCITY,
    attenuation: float = DEFAULT_ATTENUATION,
    n_samples: int = DEFAULT_N_SAMPLES,
    signal: np.ndarray | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """Add the backwall echo train: a perfect reflector at z = thickness.

    Particular case of `add_scatterer_echoes` with depth equal to the
    specimen thickness d and reflectivity 1 (steel-air backwall).
    """
    return add_scatterer_echoes(
        pulse,
        depth=thickness,
        velocity=velocity,
        attenuation=attenuation,
        sample_rate=sample_rate,
        reflectivity=1.0,
        n_samples=n_samples,
        signal=signal,
    )
