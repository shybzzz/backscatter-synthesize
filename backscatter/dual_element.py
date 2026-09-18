"""Dual-element (pitch-catch) transducer: two prisms, crossed or parallel.

A dual-element probe carries two piezo elements in one housing: a
transmitter and a receiver, each on its own plexiglass prism (delay
line) of axial length h, isolated from each other by an acoustic
barrier. The transmit axis enters the specimen at x = -a, the receive
axis at x = +a (2a = separation of the beam entry points). The prisms
may be inclined toward each other by a small roof angle theta_p, so
that the beams cross under the surface (README, section 8), or be
parallel, theta_p = 0 — the working assumption of the project for the
"straight" (укр. «прямий») probe П112-10-6/2-А-01 (README,
section 8.1). Compared with the single-element delay-line probe of
backscatter.transducer this changes three things.

1. Refraction and crossing depth. The beam axis meets the
   plexiglass-steel interface at the incidence angle theta_p and is
   refracted into the steel at the angle beta given by Snell's law,

       sin(beta) / c = sin(theta_p) / c_p,

   i.e. more than doubled for c / c_p ~ 2.2. The axes cross at the
   focal depth

       z_F = a / tan(beta),

   infinite for parallel beams. The construction parameters are a and
   theta_p; z_F is derived (`focal_depth`), and `beam_half_separation`
   gives the inverse, the a that puts the crossing at a chosen z_F.

2. Depth sensitivity. Each beam is given a Gaussian lateral pressure
   profile g(x) = exp(-x**2 / (2 w**2)) of half-width w, kept constant
   over the depth range (beam divergence neglected, as in the rest of
   the model). A plane reflector at depth z returns the transmit beam
   to the surface displaced laterally by 2 z tan(beta) from its entry
   point (mirror-image method), while the receiver accepts it with the
   same profile (reciprocity); the overlap integral of the two
   Gaussians, offset by Delta = 2a - 2 z tan(beta), is proportional to
   exp(-Delta**2 / (4 w**2)):

       D(z) = exp(-(a - z tan(beta))**2 / w**2).

   For crossed beams this is a Gaussian in depth centred at z_F with
   standard deviation sigma_z = w / (sqrt(2) tan(beta)) (depth of
   field), equal to 1 at the crossing depth. For parallel beams
   (theta_p = 0) the offset is the constant 2a and

       D = exp(-a**2 / w**2)

   for every depth: the overlap of two side-by-side beams, with no
   depth selectivity in the constant-width approximation. A point
   scatterer on the axis of symmetry gives the same factor: the
   product of the transmit and receive profiles evaluated at the
   scatterer, g(a - z tan(beta))**2. For the k-th round trip the mirror
   image of the reflector lies at the unfolded depth k z, so the k-th
   echo carries D(k z); a grain scatterer at depth z_i seen by the k-th
   reverberation of the coherent pulse carries D(k d + z_i).

3. V-path. The two-way sound path in the steel for the unfolded depth
   z is L(z) = 2 sqrt(z**2 + a**2) instead of 2 z; it sets both the
   arrival time L / c and the attenuation along L. In thickness
   gauging the apparent thickness sqrt(d**2 + a**2) exceeds d by
   ~a**2 / (2 d), the classical V-path error. It does not depend on
   the roof angle, so it persists for parallel beams.

The receiver does not see the reverberation of the transmitter prism
directly; only the small fraction that leaks through the barrier
(cross-talk). It is modeled as the prism reverberation train of
section 3 scaled by the amplitude coefficient kappa (working
assumption kappa = 0.01, i.e. -40 dB). With kappa = 1 and a = 0
(then D = 1 and L = 2 z for any roof angle) the model reduces exactly
to the single-element composition of backscatter.structural_noise.

The received signal is composed from the generic engines with the
`sensitivity` = D and `path_length` = L hooks:

- cross-talk: kappa * B_j (formula (7) of the README);
- backwall train weakened by grain scattering, with D(k d) and L(k d);
- structural noise passes, one per coherent reverberation, with
  D(k d + z_i) and L(k d + z_i) for the frozen scatterer set.

Working assumptions of this stage: identical Gaussian beams of
constant width; scatterers characterized by depth only (their lateral
spread is absorbed in R_s); first-order paths only, as before; the
attenuation of the k-th noise pass is accumulated along the whole
unfolded V-path, so the pass scale carries no attenuation of its own.
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
from backscatter.structural_noise import (
    DEFAULT_BACKSCATTERED_ENERGY,
    DEFAULT_N_SCATTERERS,
    add_structural_noise,
)
from backscatter.transducer import (
    DEFAULT_PRISM_ATTENUATION,
    DEFAULT_PRISM_THICKNESS,
    DEFAULT_PRISM_VELOCITY,
)

# Roof angle of the prisms (rad). Zero = parallel beams: the working
# assumption for the "straight" probe П112-10-6/2-А-01 (README,
# section 8.1). The crossed-beam scenario of section 8 uses 3.5 deg,
# the largest catalog value of extended-range duals.
DEFAULT_ROOF_ANGLE = 0.0
CROSSED_BEAM_ROOF_ANGLE = np.deg2rad(3.5)
# Half-separation a of the beam entry points: centroid of a half-disc
# of the 6 mm element (4R/(3 pi) ~ 1.27 mm) plus half the barrier
# (working assumption, README section 8.1).
DEFAULT_HALF_SEPARATION = 1.5e-3  # m
# Half-width w of the Gaussian lateral beam profile (working
# assumption for a 6 mm element split into two halves).
DEFAULT_BEAM_HALF_WIDTH = 1.5e-3  # m
# Amplitude cross-talk through the acoustic barrier (-40 dB, working
# assumption).
DEFAULT_CROSSTALK = 0.01


def refracted_angle(
    roof_angle: float = DEFAULT_ROOF_ANGLE,
    prism_velocity: float = DEFAULT_PRISM_VELOCITY,
    velocity: float = DEFAULT_VELOCITY,
) -> float:
    """Refraction angle beta in the specimen by Snell's law (rad).

    Args:
        roof_angle: Incidence angle theta_p of the beam axis at the
            prism-specimen interface, rad.
        prism_velocity: Longitudinal sound velocity in the prism, m/s.
        velocity: Longitudinal sound velocity in the specimen, m/s.
    """
    sin_beta = velocity / prism_velocity * np.sin(roof_angle)
    if not -1.0 < sin_beta < 1.0:
        raise ValueError("roof_angle exceeds the critical angle")
    return float(np.arcsin(sin_beta))


def focal_depth(
    half_separation: float = DEFAULT_HALF_SEPARATION,
    roof_angle: float = DEFAULT_ROOF_ANGLE,
    prism_velocity: float = DEFAULT_PRISM_VELOCITY,
    velocity: float = DEFAULT_VELOCITY,
) -> float:
    """Crossing depth z_F = a / tan(beta) of the beam axes, m.

    Infinite for parallel beams (roof_angle = 0).
    """
    tan_beta = np.tan(refracted_angle(roof_angle, prism_velocity, velocity))
    if tan_beta == 0.0:
        return float("inf")
    return float(half_separation / tan_beta)


def beam_half_separation(
    focal_depth: float,
    roof_angle: float = CROSSED_BEAM_ROOF_ANGLE,
    prism_velocity: float = DEFAULT_PRISM_VELOCITY,
    velocity: float = DEFAULT_VELOCITY,
) -> float:
    """Half-separation a that puts the crossing of the axes at z_F.

    Inverse of `focal_depth`: a = z_F tan(beta). Zero for parallel
    beams, for which no finite z_F exists.
    """
    return focal_depth * np.tan(
        refracted_angle(roof_angle, prism_velocity, velocity)
    )


def depth_of_field(
    roof_angle: float = DEFAULT_ROOF_ANGLE,
    beam_half_width: float = DEFAULT_BEAM_HALF_WIDTH,
    prism_velocity: float = DEFAULT_PRISM_VELOCITY,
    velocity: float = DEFAULT_VELOCITY,
) -> float:
    """Standard deviation sigma_z = w / (sqrt(2) tan(beta)) of D(z), m.

    Infinite for roof_angle = 0 (parallel beams, no depth selectivity).
    """
    tan_beta = np.tan(refracted_angle(roof_angle, prism_velocity, velocity))
    if tan_beta == 0.0:
        return float("inf")
    return float(beam_half_width / (np.sqrt(2.0) * tan_beta))


def depth_sensitivity(
    depth: float | np.ndarray,
    half_separation: float = DEFAULT_HALF_SEPARATION,
    roof_angle: float = DEFAULT_ROOF_ANGLE,
    beam_half_width: float = DEFAULT_BEAM_HALF_WIDTH,
    prism_velocity: float = DEFAULT_PRISM_VELOCITY,
    velocity: float = DEFAULT_VELOCITY,
) -> float | np.ndarray:
    """Depth sensitivity D(z) = exp(-(a - z tan(beta))^2 / w^2).

    Overlap of the Gaussian transmit and receive beams for a plane
    reflector (or an on-axis point scatterer) at the unfolded one-way
    depth `depth`: equals 1 at the crossing depth z_F = a / tan(beta)
    of inclined beams and the constant exp(-a^2 / w^2) for parallel
    beams. Accepts scalars and NumPy arrays.
    """
    tan_beta = np.tan(refracted_angle(roof_angle, prism_velocity, velocity))
    offset = half_separation - tan_beta * np.asarray(depth, dtype=float)
    return np.exp(-(offset / beam_half_width) ** 2)


def v_path_length(
    depth: float | np.ndarray,
    half_separation: float = DEFAULT_HALF_SEPARATION,
) -> float | np.ndarray:
    """Two-way V-path 2 sqrt(z^2 + a^2) in the specimen, m.

    Args:
        depth: Unfolded one-way depth z of the reflector, m.
        half_separation: Half-separation a of the beam entry points, m.
    """
    return 2.0 * np.sqrt(np.asarray(depth, dtype=float) ** 2 + half_separation**2)


def synthesize_dual_element_signal(
    pulse: np.ndarray,
    sample_rate: float = DEFAULT_SAMPLE_RATE,
    prism_thickness: float = DEFAULT_PRISM_THICKNESS,
    prism_velocity: float = DEFAULT_PRISM_VELOCITY,
    prism_attenuation: float = DEFAULT_PRISM_ATTENUATION,
    transmitted_energy: float = DEFAULT_CONTACT_TRANSMITTED_ENERGY,
    roof_angle: float = DEFAULT_ROOF_ANGLE,
    half_separation: float = DEFAULT_HALF_SEPARATION,
    beam_half_width: float = DEFAULT_BEAM_HALF_WIDTH,
    crosstalk: float = DEFAULT_CROSSTALK,
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
    """Synthesize the received signal of a dual-element probe.

    Composes the barrier cross-talk, the backwall train (weakened by
    grain scattering, weighted by the depth sensitivity D and timed
    along the V-path) and the structural noise re-illuminated at every
    reverberation of the coherent pulse. The random draws (depths,
    then signs) follow the same order as
    `synthesize_structural_signal`, so the same seed yields the same
    microstructure for both probes.

    Args:
        pulse: Excitation pulse samples (already at `sample_rate`).
        sample_rate: Sampling rate in Hz.
        prism_thickness: Axial length h of each prism in meters.
        prism_velocity: Longitudinal sound velocity in the prism, m/s.
        prism_attenuation: Prism attenuation in dB/m at the carrier
            frequency.
        transmitted_energy: Fraction T of the energy passed through
            the plexiglass-steel contact; must be in (0, 1).
        roof_angle: Roof angle theta_p of the prisms in radians; 0
            for parallel beams (the project default).
        half_separation: Half-separation a of the beam entry points
            in meters.
        beam_half_width: Half-width w of the Gaussian lateral beam
            profile in meters.
        crosstalk: Amplitude coefficient kappa of the transmitter
            prism reverberation leaking to the receiver; in [0, 1].
        thickness: Specimen thickness d in meters.
        velocity: Longitudinal sound velocity in the specimen, m/s.
        attenuation: Absorption component of the specimen attenuation
            in dB/m at the carrier frequency (README, section 7).
        backscattered_energy: Total energy fraction R_s backscattered
            by the grains over one pass; must be in [0, 1).
        n_scatterers: Number of grain scatterers N.
        depths: Optional scatterer depths in meters; drawn uniformly
            on (0, thickness) if omitted.
        rng: Seed or numpy Generator for reproducible realizations.
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
    if not 0.0 <= crosstalk <= 1.0:
        raise ValueError("crosstalk must be in [0, 1]")
    if not 0.0 <= backscattered_energy < 1.0:
        raise ValueError("backscattered_energy must be in [0, 1)")
    if half_separation < 0.0:
        raise ValueError("half_separation must be non-negative")
    contact_reflectivity = np.sqrt(1.0 - transmitted_energy)
    rng = np.random.default_rng(rng)
    if depths is None:
        depths = rng.uniform(0.0, thickness, n_scatterers)
    depths = np.sort(np.asarray(depths, dtype=float))
    n_scatterers = len(depths)
    signs = rng.choice((-1.0, 1.0), n_scatterers)

    def sensitivity(z):
        return depth_sensitivity(
            z, half_separation, roof_angle, beam_half_width,
            prism_velocity, velocity,
        )

    def path_length(z):
        return v_path_length(z, half_separation)

    # Family 1: cross-talk — the transmitter prism reverberation (7)
    # leaking through the barrier with amplitude coefficient kappa.
    t, signal = add_scatterer_echoes(
        pulse,
        depth=prism_thickness,
        velocity=prism_velocity,
        attenuation=prism_attenuation,
        sample_rate=sample_rate,
        reflectivity=contact_reflectivity,
        scale=crosstalk,
        n_samples=n_samples,
        signal=signal,
    )

    prism_delay = 2 * prism_thickness / prism_velocity
    prism_loss = 10 ** (-prism_attenuation * 2 * prism_thickness / 20)
    scale = transmitted_energy * prism_loss / contact_reflectivity

    # Family 2: backwall train weakened by scattering, weighted by
    # D(k d) and delayed/attenuated along the V-path L(k d).
    t, signal = add_scatterer_echoes(
        pulse,
        depth=thickness,
        velocity=velocity,
        attenuation=attenuation,
        sample_rate=sample_rate,
        reflectivity=(1.0 - backscattered_energy) * contact_reflectivity,
        scale=scale,
        time_offset=prism_delay,
        sensitivity=sensitivity,
        path_length=path_length,
        signal=signal,
    )

    # Family 3: structural noise, one pass per coherent reverberation.
    # The pass scale carries the interface reflections and scattering
    # losses of the earlier round trips; attenuation and the depth
    # sensitivity are evaluated inside add_structural_noise along the
    # unfolded V-path of each scatterer (depth_offset = k d).
    pass_factor = contact_reflectivity * (1.0 - backscattered_energy)
    round_trip_loss = 10 ** (-attenuation * 2 * thickness / 20)
    k = 0
    while True:
        pass_scale = scale * pass_factor**k
        # Stop on the COLLECTIVE noise amplitude of the pass (bounded
        # by D <= 1), not on the vanishing per-scatterer amplitude.
        collective = (
            abs(pass_scale) * round_trip_loss**k * np.sqrt(backscattered_energy)
        )
        if collective < ECHO_AMPLITUDE_FLOOR:
            break
        first_arrival = prism_delay + path_length(k * thickness) / velocity
        if round(first_arrival * sample_rate) >= n_samples:
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
            time_offset=prism_delay,
            depth_offset=k * thickness,
            sensitivity=sensitivity,
            path_length=path_length,
            rng=rng,
            n_samples=n_samples,
            signal=signal,
        )
        k += 1
    return t, signal
