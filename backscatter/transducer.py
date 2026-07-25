"""Delay-line transducer model: piezo element on a plexiglass prism.

The piezo element is glued to the top face of a plexiglass (PMMA)
prism of thickness h; the bottom face of the prism contacts the steel
specimen. The transmitted pulse crosses the prism; at the
plexiglass-steel interface a fraction T of its ENERGY passes into the
steel and the fraction 1 - T is reflected back into the prism. For
amplitudes this means a reflection coefficient

    r = sqrt(1 - T),

and, by the Stokes relations, a two-way (down + up) amplitude
transmission product t_down * t_up = 1 - r**2 = T.

The received signal is composed of two echo families, both built with
backscatter.echoes.add_scatterer_echoes:

1. Prism reverberation: the pulse bounces between the piezo-backed
   top face (|R| ~ 1 assumed) and the interface. Echo j arrives at
   t_j = j * 2h/c_p with amplitude

       B_j = r**j * 10 ** (-alpha_p * 2 h j / 20).

2. Specimen (backwall) train seen through the prism: the transmitted
   part reverberates in the steel as in the specimen model; each k-th
   backwall echo has crossed the interface twice (factor T), traversed
   the prism twice (factor 10**(-alpha_p * 2h/20), delay 2h/c_p) and
   has been reflected back into the steel by the interface k - 1
   times (factor r**(k-1)):

       A_k = T * r**(k-1) * 10 ** (-alpha_p * 2h/20)
               * 10 ** (-alpha_s * 2 d k / 20),

   arriving at t_k = 2h/c_p + k * 2d/c_s. Implemented as a scatterer
   train with reflectivity r, scale S = T * 10**(-alpha_p*2h/20) / r
   and time offset 2h/c_p.

Working assumptions of this stage:

- the piezo-backed top face of the prism is a perfect reflector;
- only first-order path families are kept: mixed paths (prism
  reverberations that re-enter the steel, and steel reverberations
  that re-enter the prism cavity) are neglected;
- the energy split T = 0.8 into steel / 0.2 back into the prism is a
  project working assumption (owner's spec, to be randomized later);
  the physical value would follow from the acoustic impedances and
  the contact condition;
- T must be < 1 (some reflection at the interface, r > 0).
"""

import numpy as np

from backscatter.echoes import DEFAULT_N_SAMPLES, add_scatterer_echoes
from backscatter.pulse import DEFAULT_SAMPLE_RATE
from backscatter.specimen import (
    DEFAULT_ATTENUATION,
    DEFAULT_THICKNESS,
    DEFAULT_VELOCITY,
)

DEFAULT_PRISM_THICKNESS = 10e-3  # m
DEFAULT_PRISM_VELOCITY = 2730.0  # m/s, longitudinal wave in plexiglass
DEFAULT_PRISM_ATTENUATION = 640.0  # dB/m (6.4 dB/cm reference value)
DEFAULT_TRANSMITTED_ENERGY = 0.8  # fraction of energy passed into steel

# Acoustic impedances in Rayl (kg/(m^2 s)); README, table 4. Used to
# evaluate the physically justified range of DEFAULT_TRANSMITTED_ENERGY
# (README, section 4) and, later, to randomize the contact condition.
IMPEDANCE_STEEL = 46.0e6
IMPEDANCE_PLEXIGLASS = 3.26e6
IMPEDANCE_GLYCERIN = 2.34e6
IMPEDANCE_WATER = 1.48e6
IMPEDANCE_AIR = 400.0


def interface_transmitted_energy(z1: float, z2: float) -> float:
    """Energy transmission coefficient of a plane interface.

    Normal incidence: T = 4 z1 z2 / (z1 + z2)**2 (README, formula (9));
    symmetric in z1 <-> z2. For the ideal plexiglass-steel contact this
    evaluates to ~0.25 — the physical ceiling for the transmitted
    energy fraction of the direct (couplant-wetted) contact.

    Args:
        z1: Acoustic impedance of the first medium, Rayl.
        z2: Acoustic impedance of the second medium, Rayl.
    """
    return 4.0 * z1 * z2 / (z1 + z2) ** 2


def synthesize_transducer_signal(
    pulse: np.ndarray,
    sample_rate: float = DEFAULT_SAMPLE_RATE,
    prism_thickness: float = DEFAULT_PRISM_THICKNESS,
    prism_velocity: float = DEFAULT_PRISM_VELOCITY,
    prism_attenuation: float = DEFAULT_PRISM_ATTENUATION,
    transmitted_energy: float = DEFAULT_TRANSMITTED_ENERGY,
    thickness: float = DEFAULT_THICKNESS,
    velocity: float = DEFAULT_VELOCITY,
    attenuation: float = DEFAULT_ATTENUATION,
    n_samples: int = DEFAULT_N_SAMPLES,
    signal: np.ndarray | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """Synthesize the received signal of the delay-line transducer.

    Adds both echo families (prism reverberation and the backwall
    train seen through the prism) to the signal.

    Args:
        pulse: Excitation pulse samples (already at `sample_rate`).
        sample_rate: Sampling rate in Hz.
        prism_thickness: Prism thickness h in meters.
        prism_velocity: Longitudinal sound velocity in the prism, m/s.
        prism_attenuation: Prism attenuation in dB/m at the carrier
            frequency.
        transmitted_energy: Fraction T of the pulse energy passed
            through the plexiglass-steel interface; must be < 1.
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
    reflectivity = np.sqrt(1.0 - transmitted_energy)

    # Family 1: reverberation inside the prism.
    t, signal = add_scatterer_echoes(
        pulse,
        depth=prism_thickness,
        velocity=prism_velocity,
        attenuation=prism_attenuation,
        sample_rate=sample_rate,
        reflectivity=reflectivity,
        n_samples=n_samples,
        signal=signal,
    )

    # Family 2: backwall train observed through the prism. The scale
    # S = T * prism_loss / r turns the generic r**k amplitude law into
    # T * r**(k-1) * prism_loss (one interface reflection less than
    # round trips, two interface crossings, two prism traversals).
    prism_delay = 2 * prism_thickness / prism_velocity
    prism_loss = 10 ** (-prism_attenuation * 2 * prism_thickness / 20)
    scale = transmitted_energy * prism_loss / reflectivity
    return add_scatterer_echoes(
        pulse,
        depth=thickness,
        velocity=velocity,
        attenuation=attenuation,
        sample_rate=sample_rate,
        reflectivity=reflectivity,
        scale=scale,
        time_offset=prism_delay,
        signal=signal,
    )
