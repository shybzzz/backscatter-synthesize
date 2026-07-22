# backscatter-synthesize

Numerical synthesis of the backscattered signal of a dual-element (pitch-catch, укр. «роздільно-суміщений») ultrasonic piezoelectric transducer for NDT (flaw detection, thickness gauging). The model is built incrementally, stage by stage of the physical signal chain; the owner describes each next stage before it is implemented — do not implement stages ahead of being asked.

## Commands

- Run: `python main.py` (writes figures to `images/`, then opens plot windows)
- Install deps: `pip install -r requirements.txt` (NumPy, SciPy, matplotlib; Python >= 3.10)
- No test suite yet.

## Structure

- `main.py` — entry point; builds the signal chain, saves plots to `images/`
- `backscatter/pulse.py` — excitation pulse generation (Gaussian-enveloped sine)
- `backscatter/visualization.py` — matplotlib helpers; `plot_signal(..., save_path=)` creates parent dirs automatically
- `images/` — generated figures, committed to the repo and embedded in README (subfolders may be added per model stage)

## Conventions

- Code, comments, and docstrings: English. Documentation (README): Ukrainian — see the `readme` skill for style, terminology, and enumeration rules.
- Physical defaults live as module-level constants (e.g. `DEFAULT_FREQUENCY = 10e6`); every physical parameter is a function argument with such a default, units in Hz/seconds, SI throughout.
- Signal functions return `(t, signal)` NumPy array pairs of equal length, `t` in seconds.
- Plots display time in microseconds (µs).
- When a new model stage is added: implement it in its own module under `backscatter/`, wire it into `main.py`, regenerate figures, and update README (via the `readme` skill) including the roadmap checklist.
