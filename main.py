"""Entry point: synthesize backscattered signal from a dual-element transducer."""

from pathlib import Path

import numpy as np

from backscatter.flaw import synthesize_flaw_signal
from backscatter.pulse import generate_pulse
from backscatter.structural_noise import synthesize_structural_signal
from backscatter.schematic import (
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


if __name__ == "__main__":
    main()
