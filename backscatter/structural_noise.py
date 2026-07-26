"""Structural (grain) noise: backscatter from many small scatterers.

The specimen material contains N small scatterers at random depths
z_i in (0, d) — uniformly distributed by default. Grain scattering is
the physical source of both structural noise and the scattering part
of attenuation in metals (README, section 6). Each scatterer reflects
back the small energy fraction eps, identical for all, fixed by the
requirement that the TOTAL backscattered energy of one full pass
through the specimen equals R_s:

    1 - (1 - eps)**N = R_s   =>   eps = 1 - (1 - R_s)**(1/N),

with amplitude reflection r_s = sqrt(eps) and, by the Stokes
relations, the amplitude factor (1 - eps) for a two-way crossing of
one scatterer. In the single-scattering (first-order) approximation
the scatterer at depth z_i, with n_i scatterers above it, returns the
echo

    A_i = S * s_i * r_s * (1 - eps)**n_i * 10**(-alpha*2*z_i/20)

at t_i = t_0 + 2 z_i / c, where s_i = +-1 is a random sign (the
impedance fluctuation may have either polarity) and S, t_0 are the
transfer scale and delay of the path to the specimen surface.

Two consequences for the composed signal:

- the coherent wave loses the amplitude factor (1 - eps)**N = 1 - R_s
  per round trip, so the backwall train weakens by (1 - R_s)**k —
  scattering attenuation arises automatically and does not depend on
  the particular N;
- the microstructure is frozen, so every reverberation of the
  coherent pulse re-illuminates the SAME scatterer set: the noise
  pattern repeats at t_0 + k*tau, scaled like the backwall train.

Neglected (working assumptions): multiple scattering (echoes that
involve more than one scatterer), scattering of the upward-returning
coherent wave, and reverberation of the noise itself.

Note on attenuation bookkeeping: with structural noise enabled the
scattering part of attenuation is carried by R_s (equivalent to
~220 dB/m at the defaults), so the `attenuation` parameter should be
read as the ABSORPTION component only. Measured attenuation values
(like the 20 dB/m steel default) already include grain scattering,
so the defaults slightly double-count it; when calibrating to a real
material, split the measured attenuation between `attenuation` and
`backscattered_energy` deliberately (README, section 6).
"""

import numpy as np

from backscatter.echoes import (
    DEFAULT_N_SAMPLES,
    ECHO_AMPLITUDE_FLOOR,
    add_scatterer_echoes,
)
from backscatter.flaw import DEFAULT_CONTACT_TRANSMITTED_ENERGY
from backscatter.pulse import DEFAULT_SAMPLE_RATE
from backscatter.specimen import (
    DEFAULT_ATTENUATION,
    DEFAULT_THICKNESS,
    DEFAULT_VELOCITY,
)
from backscatter.transducer import (
    DEFAULT_PRISM_ATTENUATION,
    DEFAULT_PRISM_THICKNESS,
    DEFAULT_PRISM_VELOCITY,
)

# Sized so that Poisson fluctuations of the per-bin scatterer count
# stay within 1 %: N = m / delta**2 with m = 20 depth bins and
# delta = 0.01 (README, section 6, formula (16)).
DEFAULT_N_SCATTERERS = 200_000
DEFAULT_BACKSCATTERED_ENERGY = 0.4  # total over one full pass


def add_structural_noise(
    pulse: np.ndarray,
    sample_rate: float = DEFAULT_SAMPLE_RATE,
    thickness: float = DEFAULT_THICKNESS,
    velocity: float = DEFAULT_VELOCITY,
    attenuation: float = DEFAULT_ATTENUATION,
    backscattered_energy: float = DEFAULT_BACKSCATTERED_ENERGY,
    n_scatterers: int = DEFAULT_N_SCATTERERS,
    depths: np.ndarray | None = None,
    signs: np.ndarray | None = None,
    scale: float = 1.0,
    time_offset: float = 0.0,
    rng: np.random.Generator | int | None = None,
    n_samples: int = DEFAULT_N_SAMPLES,
    signal: np.ndarray | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """Add one pass of structural backscatter to a signal.

    Args:
        pulse: Excitation pulse samples (already at `sample_rate`).
        sample_rate: Sampling rate in Hz.
        thickness: Specimen thickness d in meters.
        velocity: Longitudinal sound velocity c in m/s.
        attenuation: Attenuation coefficient in dB/m at the carrier
            frequency.
        backscattered_energy: Total energy fraction R_s backscattered
            over one full pass; must be in [0, 1).
        n_scatterers: Number of scatterers N on the wave's path; the
            default keeps Poisson fluctuations of the depth density
            within 1 % per bin (README, formula (16)).
        depths: Optional scatterer depths in meters (any custom
            spatial distribution); drawn uniformly on (0, thickness)
            if omitted. Sorted internally; `signs`, if given, must
            correspond to the sorted order.
        signs: Optional +-1 sign per scatterer; drawn randomly if
            omitted. Pass explicitly to keep the microstructure
            frozen across repeated passes.
        scale: Transfer amplitude factor S of the path to the
            specimen surface.
        time_offset: Transfer delay t_0 in seconds.
        rng: Seed or numpy Generator for reproducible realizations.
        n_samples: Length of the result signal; ignored if `signal`
            is given.
        signal: Optional existing signal to add to; not modified, a
            copy is returned.

    Returns:
        (t, signal): time vector in seconds and the signal with the
        noise added, both of length `n_samples`.
    """
    if not 0.0 <= backscattered_energy < 1.0:
        raise ValueError("backscattered_energy must be in [0, 1)")
    if n_scatterers < 1:
        raise ValueError("n_scatterers must be positive")
    rng = np.random.default_rng(rng)

    if depths is None:
        depths = rng.uniform(0.0, thickness, n_scatterers)
    else:
        depths = np.asarray(depths, dtype=float)
        n_scatterers = len(depths)
    depths = np.sort(depths)
    if signs is None:
        signs = rng.choice((-1.0, 1.0), n_scatterers)

    if signal is None:
        signal = np.zeros(n_samples)
    else:
        signal = np.asarray(signal, dtype=float).copy()
        n_samples = len(signal)
    t = np.arange(n_samples) / sample_rate

    eps = 1.0 - (1.0 - backscattered_energy) ** (1.0 / n_scatterers)
    r_s = np.sqrt(eps)
    amplitudes = (
        scale * signs * r_s * (1.0 - eps) ** np.arange(n_scatterers)
        * 10 ** (-attenuation * 2 * depths / 20)
    )
    starts = np.rint(
        (time_offset + 2 * depths / velocity) * sample_rate
    ).astype(int)
    keep = starts < n_samples
    starts, amplitudes = starts[keep], amplitudes[keep]
    # Vectorized scatter-add: one bincount per pulse sample.
    for j, p_j in enumerate(pulse):
        idx = starts + j
        m = idx < n_samples
        signal += np.bincount(
            idx[m], weights=amplitudes[m] * p_j, minlength=n_samples
        )
    return t, signal


def synthesize_structural_signal(
    pulse: np.ndarray,
    sample_rate: float = DEFAULT_SAMPLE_RATE,
    prism_thickness: float = DEFAULT_PRISM_THICKNESS,
    prism_velocity: float = DEFAULT_PRISM_VELOCITY,
    prism_attenuation: float = DEFAULT_PRISM_ATTENUATION,
    transmitted_energy: float = DEFAULT_CONTACT_TRANSMITTED_ENERGY,
    thickness: float = DEFAULT_THICKNESS,
    velocity: float = DEFAULT_VELOCITY,
    attenuation: float = DEFAULT_ATTENUATION,
    backscattered_energy: float = DEFAULT_BACKSCATTERED_ENERGY,
    n_scatterers: int = DEFAULT_N_SCATTERERS,
    depths: np.ndarray | None = None,
    rng: np.random.Generator | int | None = None,
    n_samples: int = DEFAULT_N_SAMPLES,
    signal: np.ndarray | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """Synthesize the delay-line transducer signal with grain noise.

    Composes the prism reverberation, the backwall train weakened by
    scattering (extra factor (1 - R_s) per round trip) and the
    structural noise re-illuminated at every reverberation of the
    coherent pulse.

    Args and returns: as in `synthesize_transducer_signal` and
    `add_structural_noise`.
    """
    if not 0.0 < transmitted_energy < 1.0:
        raise ValueError("transmitted_energy must be in (0, 1)")
    contact_reflectivity = np.sqrt(1.0 - transmitted_energy)
    rng = np.random.default_rng(rng)
    # The microstructure is frozen: one realization of depths and
    # signs is shared by all passes.
    if depths is None:
        depths = rng.uniform(0.0, thickness, n_scatterers)
    depths = np.sort(np.asarray(depths, dtype=float))
    n_scatterers = len(depths)
    signs = rng.choice((-1.0, 1.0), n_scatterers)

    # Family 1: reverberation inside the prism (section 3).
    t, signal = add_scatterer_echoes(
        pulse,
        depth=prism_thickness,
        velocity=prism_velocity,
        attenuation=prism_attenuation,
        sample_rate=sample_rate,
        reflectivity=contact_reflectivity,
        n_samples=n_samples,
        signal=signal,
    )

    prism_delay = 2 * prism_thickness / prism_velocity
    prism_loss = 10 ** (-prism_attenuation * 2 * prism_thickness / 20)
    scale = transmitted_energy * prism_loss / contact_reflectivity

    # Family 2: backwall train, additionally weakened by scattering.
    t, signal = add_scatterer_echoes(
        pulse,
        depth=thickness,
        velocity=velocity,
        attenuation=attenuation,
        sample_rate=sample_rate,
        reflectivity=(1.0 - backscattered_energy) * contact_reflectivity,
        scale=scale,
        time_offset=prism_delay,
        signal=signal,
    )

    # Family 3: structural noise, one pass per coherent reverberation
    # (same frozen scatterer set, scaled like the backwall train).
    round_trip = 2 * thickness / velocity
    pass_factor = (
        contact_reflectivity
        * (1.0 - backscattered_energy)
        * 10 ** (-attenuation * 2 * thickness / 20)
    )
    k = 0
    while True:
        pass_scale = scale * pass_factor**k
        # Stop on the COLLECTIVE noise amplitude of the pass
        # (~ sqrt of its total backscattered energy), not on the
        # vanishing per-scatterer amplitude.
        if abs(pass_scale) * np.sqrt(backscattered_energy) < ECHO_AMPLITUDE_FLOOR:
            break
        offset = prism_delay + k * round_trip
        if round(offset * sample_rate) >= n_samples:
            break
        t, signal = add_structural_noise(
            pulse,
            sample_rate=sample_rate,
            thickness=thickness,
            velocity=velocity,
            attenuation=attenuation,
            backscattered_energy=backscattered_energy,
            n_scatterers=n_scatterers,
            depths=depths,
            signs=signs,
            scale=pass_scale,
            time_offset=offset,
            rng=rng,
            n_samples=n_samples,
            signal=signal,
        )
        k += 1
    return t, signal
