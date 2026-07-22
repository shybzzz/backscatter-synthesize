"""Entry point: synthesize backscattered signal from a dual-element transducer."""

from pathlib import Path

from backscatter.pulse import generate_pulse
from backscatter.schematic import draw_schematic
from backscatter.specimen import add_backwall_echoes
from backscatter.visualization import plot_signal

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

    t, signal = add_backwall_echoes(pulse)
    plot_signal(
        t,
        signal,
        title="Backwall echo train (10 mm steel specimen)",
        save_path=IMAGES_DIR / "echoes.png",
    )


if __name__ == "__main__":
    main()
