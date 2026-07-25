"""Flawed specimen model: a partial plane reflector inside the steel.

A flaw lies at depth z_f below the outer surface of the specimen
(z_f < d). Of the energy incident on it, the fraction R_f is reflected
back and 1 - R_f passes on toward the backwall. For amplitudes this
means (README, section 5)

    r_f = sqrt(R_f),          # reflection, from R = r**2
    t_down * t_up = 1 - r_f**2 = T_f,   # Stokes: two-way transmission

so every round trip that crosses the flaw twice keeps the amplitude
factor T_f. Together with the delay-line prism of section 3 (contact
transmission T, r = sqrt(1 - T)) the received signal consists of
three echo families, all built with add_scatterer_echoes and sharing
the transfer scale S = T * 10**(-alpha_p*2h/20) / r and the prism
delay t_0 = 2h/c_p:

1. prism reverberation — as in section 3, formula (7);
2. flaw train, reverberation between the interface and the flaw:
   k-th echo reflects k times off the flaw and k-1 times off the
   interface,
       A_k = T * r**(k-1) * r_f**k * 10**(-alpha_p*2h/20)
               * 10**(-alpha * 2 z_f k / 20),
   at t_k = 2h/c_p + k * 2 z_f / c  — generic train with
   reflectivity r_f * r;
3. backwall train seen through the flaw: k-th echo additionally
   crosses the flaw 2k times,
       A_k = T * r**(k-1) * T_f**k * 10**(-alpha_p*2h/20)
               * 10**(-alpha * 2 d k / 20),
   at t_k = 2h/c_p + k * 2 d / c — generic train with
   reflectivity T_f * r.

With R_f = 0 (no flaw) family 2 vanishes and family 3 reduces to the
section 3 model. Working assumptions: the flaw is a plane partial
reflector covering the whole beam; reverberations between the flaw
and the backwall (second order in r_f) and other mixed paths are
neglected; note that in the special case z_f = d/2 the flaw echoes
with even k coincide in time with backwall echoes and add coherently
(the default z_f = 0.3 d avoids this edge case).
"""

import numpy as np

from backscatter.echoes import DEFAULT_N_SAMPLES, add_scatterer_echoes
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

DEFAULT_FLAW_DEPTH = 3e-3  # m
DEFAULT_FLAW_REFLECTED_ENERGY = 0.4  # fraction of incident energy
# Contact transmission for the flaw scenario: the physically justified
# value from README, section 4 (not the optimistic section-3 default).
DEFAULT_CONTACT_TRANSMITTED_ENERGY = 0.2


def synthesize_flaw_signal(
    pulse: np.ndarray,
    sample_rate: float = DEFAULT_SAMPLE_RATE,
    prism_thickness: float = DEFAULT_PRISM_THICKNESS,
    prism_velocity: float = DEFAULT_PRISM_VELOCITY,
    prism_attenuation: float = DEFAULT_PRISM_ATTENUATION,
    transmitted_energy: float = DEFAULT_CONTACT_TRANSMITTED_ENERGY,
    flaw_depth: float = DEFAULT_FLAW_DEPTH,
    flaw_reflected_energy: float = DEFAULT_FLAW_REFLECTED_ENERGY,
    thickness: float = DEFAULT_THICKNESS,
    velocity: float = DEFAULT_VELOCITY,
    attenuation: float = DEFAULT_ATTENUATION,
    n_samples: int = DEFAULT_N_SAMPLES,
    signal: np.ndarray | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """Synthesize the received signal of a flawed specimen.

    Adds all three echo families (prism reverberation, flaw train,
    backwall train through the flaw) to the signal.

    Args:
        pulse: Excitation pulse samples (already at `sample_rate`).
        sample_rate: Sampling rate in Hz.
        prism_thickness: Prism thickness h in meters.
        prism_velocity: Longitudinal sound velocity in the prism, m/s.
        prism_attenuation: Prism attenuation in dB/m at the carrier
            frequency.
        transmitted_energy: Fraction T of the energy passed through
            the plexiglass-steel contact; must be in (0, 1).
        flaw_depth: Flaw depth z_f below the outer surface in meters;
            must be smaller than `thickness`.
        flaw_reflected_energy: Fraction R_f of the incident energy the
            flaw reflects backward; must be in [0, 1).
        thickness: Specimen thickness d in meters.
        velocity: Longitudinal sound velocity in the specimen, m/s.
        attenuation: Specimen attenuation in dB/m at the carrier
            frequency.
        n_samples: Length of the result signal; ignored if `signal`
            is given.
        signal: Optional existing signal to add to; not modified, a
            copy is returned.

    Returns:
        (t, signal): time vector in seconds and the synthesized
        signal, both of length `n_samples`.
    """
    if not 0.0 < transmitted_energy < 1.0:
        raise ValueError("transmitted_energy must be in (0, 1)")
    if not 0.0 <= flaw_reflected_energy < 1.0:
        raise ValueError("flaw_reflected_energy must be in [0, 1)")
    if not 0.0 < flaw_depth < thickness:
        raise ValueError("flaw_depth must be in (0, thickness)")

    contact_reflectivity = np.sqrt(1.0 - transmitted_energy)
    flaw_reflectivity = np.sqrt(flaw_reflected_energy)
    flaw_transmission = 1.0 - flaw_reflected_energy

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

    # Family 2: reverberation between the interface and the flaw.
    t, signal = add_scatterer_echoes(
        pulse,
        depth=flaw_depth,
        velocity=velocity,
        attenuation=attenuation,
        sample_rate=sample_rate,
        reflectivity=flaw_reflectivity * contact_reflectivity,
        scale=scale,
        time_offset=prism_delay,
        signal=signal,
    )

    # Family 3: backwall train crossing the flaw twice per round trip.
    return add_scatterer_echoes(
        pulse,
        depth=thickness,
        velocity=velocity,
        attenuation=attenuation,
        sample_rate=sample_rate,
        reflectivity=flaw_transmission * contact_reflectivity,
        scale=scale,
        time_offset=prism_delay,
        signal=signal,
    )
