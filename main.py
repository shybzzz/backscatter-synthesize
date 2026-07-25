"""Entry point: synthesize backscattered signal from a dual-element transducer."""

from pathlib import Path

from backscatter.flaw import synthesize_flaw_signal
from backscatter.pulse import generate_pulse
from backscatter.schematic import (
    draw_flaw_schematic,
    draw_prism_schematic,
    draw_schematic,
)
from backscatter.specimen import add_backwall_echoes
from backscatter.transducer import synthesize_transducer_signal
from backscatter.visualization import plot_signal, plot_signals

IMAGES_DIR = Path(__file__).parent / "images"


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
    )

    t, signal = synthesize_transducer_signal(pulse)
    plot_signal(
        t,
        signal,
        title="Delay-line transducer signal (10 mm plexiglass prism)",
        save_path=IMAGES_DIR / "transducer.png",
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
    )
    axes = plot_signals(
        t,
        [
            ("flaw at 3 mm", with_flaw),
            ("flaw at 0.3 mm (near-surface)", shallow_flaw),
        ],
        title="Near-surface flaw: merged packet (zoom)",
        show=False,
    )
    axes[0].set_xlim(6.5, 10.5)
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
    )
    axes[0].set_xlim(6.8, 9.5)
    axes[0].figure.savefig(IMAGES_DIR / "flaw_interference.png", dpi=150)

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
    )


if __name__ == "__main__":
    main()
