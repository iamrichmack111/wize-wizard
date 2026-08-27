# Manim lesson animations

Wize Wizard v0.7.0 contains a Manim scene for every guided lesson. The application also includes an interactive browser animation fallback, so learning remains usable even when the server has no Manim installation.

Render production MP4s with:

```bash
python -m pip install -e '.[animation]'
python scripts/render_lessons.py
```

The renderer writes the final lesson files into:

```text
wize_wizard/static/videos/
```

The lesson page detects the matching MP4 automatically. If present, it displays the Manim video. If absent, it displays the browser-based interactive animation instead.

Current scenes cover:

- Connected Wize Why ladder
- Program Evaluation and Review Technique (PERT) / stress
- Communication channels and supervision
- Strategy learning loop
- Henderson / BCG relative position
- MECE issue trees
- Porter's Five Forces
- Four-Firm Concentration Ratio / Herfindahl-Hirschman Index
- Return on Invested Capital vs Weighted Average Cost of Capital
- Monte Carlo Simulation
- Theory of Constraints / flow
- Integrated strategy decision
