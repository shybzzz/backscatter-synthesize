"""Entry point: synthesize backscattered signal from a dual-element transducer."""

from pathlib import Path

import numpy as np

from backscatter.dual_element import (
    CROSSED_BEAM_ROOF_ANGLE,
    DEFAULT_HALF_SEPARATION,
    beam_half_separation,
    depth_sensitivity,
    synthesize_dual_element_signal,
    v_path_length,
)
from backscatter.flaw import synthesize_flaw_signal
from backscatter.pulse import generate_pulse
from backscatter.structural_noise import synthesize_structural_signal
from backscatter.schematic import (
    draw_dual_element_schematic,
    draw_flaw_schematic,
    draw_prism_schematic,
    draw_schematic,
)
from backscatter.specimen import (
    DEFAULT_THICKNESS,
    DEFAULT_VELOCITY,
    add_backwall_echoes,
)
from backscatter.transducer import (
    DEFAULT_PRISM_THICKNESS,
    DEFAULT_PRISM_VELOCITY,
    synthesize_transducer_signal,
)
from backscatter.visualization import (
    plot_attenuation_components,
    plot_depth_sensitivity,
    plot_signal,
    plot_signals,
    plot_signals_with_depth_histogram,
)

IMAGES_DIR = Path(__file__).parent / "images"

# Vertical time markers for A-scans: the front surface of the specimen
# (first prism-interface echo) and the first backwall echo.
FRONT_TIME = 2 * DEFAULT_PRISM_THICKNESS / DEFAULT_PRISM_VELOCITY
BACKWALL_TIME = FRONT_TIME + 2 * DEFAULT_THICKNESS / DEFAULT_VELOCITY
MARKERS = [
    (FRONT_TIME, "green", "front surface"),
    (BACKWALL_TIME, "blue", "first backwall"),
]
# Dual-element probe (README, section 8): the first backwall echo
# travels the V-path 2 sqrt(d^2 + a^2) instead of 2 d. Crossed-beam
# scenario of section 8: roof angle 3.5 deg with the axes crossing at
# z_F = d; parallel-beam default of section 8.1: a = 1.5 mm.
HALF_SEPARATION_CROSSED = beam_half_separation(
    DEFAULT_THICKNESS, CROSSED_BEAM_ROOF_ANGLE
)
CROSSED_BEAMS = {
    "roof_angle": CROSSED_BEAM_ROOF_ANGLE,
    "half_separation": HALF_SEPARATION_CROSSED,
}


def dual_markers(half_separation: float) -> list:
    return [
        (FRONT_TIME, "green", "front surface"),
        (
            FRONT_TIME
            + v_path_length(DEFAULT_THICKNESS, half_separation) / DEFAULT_VELOCITY,
            "blue",
            "first backwall (V-path)",
        ),
    ]


MARKERS_DUAL = dual_markers(HALF_SEPARATION_CROSSED)
MARKERS_STRAIGHT = dual_markers(DEFAULT_HALF_SEPARATION)
# The bare-specimen model of README section 2 has no prism: the front
# surface is at t = 0 and the first backwall echo one round trip later.
MARKERS_BARE = [
    (0.0, "green", "front surface"),
    (2 * DEFAULT_THICKNESS / DEFAULT_VELOCITY, "blue", "first backwall"),
]


def main() -> None:
    t, pulse = generate_pulse()
    plot_signal(
        t,
        pulse,
        title="Excitation pulse (10 MHz, 7 periods)",
        save_path=IMAGES_DIR / "pulse.png",
    )

    draw_schematic(save_path=IMAGES_DIR / "scheme.png")
    draw_prism_schematic(save_path=IMAGES_DIR / "scheme_prism.png")
    draw_flaw_schematic(save_path=IMAGES_DIR / "scheme_flaw.png")

    t, signal = add_backwall_echoes(pulse)
    plot_signal(
        t,
        signal,
        title="Backwall echo train (10 mm steel specimen)",
        save_path=IMAGES_DIR / "echoes.png",
        vlines=MARKERS_BARE,
    )

    t, signal = synthesize_transducer_signal(pulse)
    plot_signal(
        t,
        signal,
        title="Delay-line transducer signal (10 mm plexiglass prism)",
        save_path=IMAGES_DIR / "transducer.png",
        vlines=MARKERS,
    )

    # Contact quality comparison: the physically justified range of the
    # interface energy transmission (README, section 4).
    contact_signals = [
        (f"T = {T:g}", synthesize_transducer_signal(pulse, transmitted_energy=T)[1])
        for T in (0.1, 0.2, 0.25)
    ]
    plot_signals(
        t,
        contact_signals,
        title="Effect of contact quality (transmitted energy T)",
        save_path=IMAGES_DIR / "transducer_contact.png",
        vlines=MARKERS,
    )

    # Flaw signature: same contact (T = 0.2) with and without a flaw
    # at 3 mm depth reflecting 40 % of the incident energy.
    t, no_flaw = synthesize_transducer_signal(pulse, transmitted_energy=0.2)
    t, with_flaw = synthesize_flaw_signal(pulse)
    plot_signals(
        t,
        [
            ("no flaw, T = 0.2", no_flaw),
            ("flaw at 3 mm, R = 0.4, T = 0.2", with_flaw),
        ],
        title="Flaw signature (10 mm steel, delay-line transducer)",
        save_path=IMAGES_DIR / "flaw.png",
        vlines=MARKERS,
    )

    # Near-surface flaw: depth much smaller than the pulse spatial
    # length (round trip ~ one carrier period), so the flaw echoes
    # overlap almost in phase, ring up and merge with the interface
    # echo — the classic dead-zone case.
    t, shallow_flaw = synthesize_flaw_signal(pulse, flaw_depth=0.3e-3)
    plot_signals(
        t,
        [
            ("flaw at 3 mm", with_flaw),
            ("flaw at 0.3 mm (near-surface)", shallow_flaw),
        ],
        title="Near-surface flaw: overlapping in-phase echoes",
        save_path=IMAGES_DIR / "flaw_shallow.png",
        vlines=MARKERS,
    )
    axes = plot_signals(
        t,
        [
            ("flaw at 3 mm", with_flaw),
            ("flaw at 0.3 mm (near-surface)", shallow_flaw),
        ],
        title="Near-surface flaw: merged packet (zoom)",
        show=False,
        vlines=MARKERS,
    )
    axes[0].set_xlim(6.5, 11.2)
    axes[0].figure.savefig(IMAGES_DIR / "flaw_shallow_zoom.png", dpi=150)

    # Interference of overlapping flaw echoes: round-trip phase
    # 2*pi*2*z_f/lambda gives in-phase pile-up at z_f = m*lambda/2 and
    # antiphase suppression at odd multiples of lambda/4
    # (lambda = c/f0 = 592 um in steel at 10 MHz).
    wavelength = 5920.0 / 10e6
    interference_signals = [
        (
            f"z_f = {name} ({z_f * 1e3:.3f} mm)",
            synthesize_flaw_signal(pulse, flaw_depth=z_f)[1],
        )
        for name, z_f in (
            ("λ/4", wavelength / 4),
            ("λ/2", wavelength / 2),
            ("3λ/4", 3 * wavelength / 4),
        )
    ]
    axes = plot_signals(
        t,
        interference_signals,
        title="Sub-wavelength flaw depth: echo interference (zoom)",
        show=False,
        vlines=MARKERS,
    )
    axes[0].set_xlim(6.8, 11.2)
    axes[0].figure.savefig(IMAGES_DIR / "flaw_interference.png", dpi=150)

    # Structural (grain) noise: 200 000 scatterers (1 % Poisson
    # deviation per depth bin), 40 % of the energy backscattered over
    # one pass; fixed seed keeps the committed figure reproducible.
    # The bottom panel shows the same realization of depths that
    # synthesize_structural_signal(rng=1) draws, unfolded onto the
    # time axis via t = t0 + 2 z / c.
    depths = np.random.default_rng(1).uniform(0.0, 10e-3, 200_000)
    t, noisy = synthesize_structural_signal(pulse, rng=1)
    plot_signals_with_depth_histogram(
        t,
        [
            ("no structural noise, T = 0.2", no_flaw),
            ("structural noise: N = 2·10⁵, R = 0.4", noisy),
        ],
        depths=depths,
        velocity=5920.0,
        time_offset=2 * 10e-3 / 2730.0,
        thickness=10e-3,
        title="Structural noise (10 mm steel, delay-line transducer)",
        save_path=IMAGES_DIR / "structural_noise.png",
        vlines=MARKERS,
    )

    # Attenuation decomposition for steel 1020 (Ono 2020, Mason-
    # McSkimin fit): damping and Rayleigh scattering cross over near
    # our 10 MHz carrier.
    plot_attenuation_components(
        np.linspace(0.5, 15.0, 300),
        damping_coefficient=7.63,
        rayleigh_coefficient=0.00861,
        marker_frequency=10.0,
        title="Steel 1020: attenuation decomposition (Ono, 2020)",
        save_path=IMAGES_DIR / "attenuation_1020.png",
    )

    # A-scans for the three physically calibrated steels of README
    # table 7: absorption-only attenuation (Cd * f0) paired with R_s
    # computed from the Rayleigh scattering component.
    calibrated_steels = [
        ("4340: $\\alpha$ = 91 dB/m, $R_s$ = 0", 91.4, 0.0),
        ("1020: $\\alpha$ = 76 dB/m, $R_s$ = 0.18", 76.3, 0.18),
        ("0.38C: $\\alpha$ = 160 dB/m, $R_s$ = 0.50", 160.0, 0.50),
    ]
    steel_signals = [
        (
            label,
            synthesize_structural_signal(
                pulse,
                attenuation=attenuation,
                backscattered_energy=backscatter,
                rng=1,
            )[1],
        )
        for label, attenuation, backscatter in calibrated_steels
    ]
    plot_signals(
        t,
        steel_signals,
        title="Calibrated steels: absorption + grain scattering (table 7)",
        save_path=IMAGES_DIR / "steels_calibrated.png",
        vlines=MARKERS,
    )

    # Flaw depth sweep: at z_f = d/2 = 5 mm the flaw and backwall
    # trains overlap (every 2nd flaw echo lands on a backwall echo).
    depth_signals = [
        (f"z_f = {mm} mm", synthesize_flaw_signal(pulse, flaw_depth=mm * 1e-3)[1])
        for mm in (3, 4, 5, 6, 7)
    ]
    plot_signals(
        t,
        depth_signals,
        title="Flaw depth vs. train overlap (d = 10 mm)",
        save_path=IMAGES_DIR / "flaw_depths.png",
        vlines=MARKERS,
    )

    # Dual-element probe (README, section 8): geometry, depth
    # sensitivity D(z) with the V-path excess, and the A-scans of
    # sections 6 and 7 re-synthesized for the crossed-beam geometry.
    draw_dual_element_schematic(save_path=IMAGES_DIR / "scheme_dual.png")
    z = np.linspace(0.0, 3 * DEFAULT_THICKNESS, 601)
    depth_marks = [(k * DEFAULT_THICKNESS, f"{k}d") for k in (1, 2, 3)]
    plot_depth_sensitivity(
        z,
        depth_sensitivity(z, **CROSSED_BEAMS),
        v_path_length(z, HALF_SEPARATION_CROSSED) / 2 - z,
        marks=depth_marks,
        focal_depth=DEFAULT_THICKNESS,
        title="Crossed beams (3.5°): depth sensitivity and V-path excess",
        save_path=IMAGES_DIR / "dual_sensitivity.png",
    )

    # Same frozen microstructure (seed 1) seen by the single-element
    # delay-line probe of section 6 and by the crossed-beam dual probe.
    t, dual_noisy = synthesize_dual_element_signal(pulse, rng=1, **CROSSED_BEAMS)
    plot_signals(
        t,
        [
            ("single element (delay line), R = 0.4", noisy),
            ("dual element (crossed beams), same microstructure", dual_noisy),
        ],
        title="Structural noise: single- vs dual-element probe",
        save_path=IMAGES_DIR / "dual_structural_noise.png",
        vlines=MARKERS_DUAL,
    )

    # Calibrated steels of table 7 with the crossed-beam dual probe.
    def steel_signals_dual(**probe):
        return [
            (
                label,
                synthesize_dual_element_signal(
                    pulse,
                    attenuation=attenuation,
                    backscattered_energy=backscatter,
                    rng=1,
                    **probe,
                )[1],
            )
            for label, attenuation, backscatter in calibrated_steels
        ]

    plot_signals(
        t,
        steel_signals_dual(**CROSSED_BEAMS),
        title="Calibrated steels, dual probe with crossed beams (table 7)",
        save_path=IMAGES_DIR / "dual_steels_calibrated.png",
        vlines=MARKERS_DUAL,
    )

    # Section 8.1: parallel beams (roof angle 0), the working assumption
    # for the "straight" probe П112-10-6/2-А-01 and the module default.
    # D(z) is then the constant exp(-a^2/w^2); the V-path stays.
    plot_depth_sensitivity(
        z,
        [
            ("$\\theta_p = 0$ (parallel beams, default)", depth_sensitivity(z)),
            ("$\\theta_p = 3.5°$ (crossed beams, section 8)",
             depth_sensitivity(z, **CROSSED_BEAMS)),
        ],
        v_path_length(z) / 2 - z,
        marks=depth_marks,
        title="Parallel beams: depth sensitivity and V-path excess",
        save_path=IMAGES_DIR / "dual_straight_sensitivity.png",
    )
    t, straight_noisy = synthesize_dual_element_signal(pulse, rng=1)
    plot_signals(
        t,
        [
            ("crossed beams, $\\theta_p = 3.5°$", dual_noisy),
            ("parallel beams, $\\theta_p = 0$", straight_noisy),
        ],
        title="Dual-element probe: crossed vs parallel beams",
        save_path=IMAGES_DIR / "dual_straight_noise.png",
        vlines=MARKERS_STRAIGHT,
    )
    plot_signals(
        t,
        steel_signals_dual(),
        title="Calibrated steels, dual probe with parallel beams (table 7)",
        save_path=IMAGES_DIR / "dual_straight_steels.png",
        vlines=MARKERS_STRAIGHT,
    )


if __name__ == "__main__":
    main()
