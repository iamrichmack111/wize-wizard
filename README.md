# 🧙 Wize Wizard v0.3

A keyboard-first Textual strategy, uncertainty, communications, and execution journal.

## Structured grammar

Every strategy statement, automatic Why, and manually added task uses:

```text
As a ______________________  [optional]
I need to __________________
so that I can ______________
because ____________________ [optional]
```

Users **do not choose** Need / Want / Wish / Dream. For each Lafley question, Wize Wizard advances the ladder automatically in the background:

`Initial Need → Want → Wish → Dream`

Each saved strategy statement is automatically copied into the linked project task list. `because` statements are also linked into **Clay Tablets**.

## Lafley questions

- What is Winning?
- Where Will I Play?
- What Tools Do I Need?
- What Skills Do I Need?
- What Management Systems Do I Need?

## PERT and stress

Full PERT now accepts **Best Case / Worst Case** values and automatically calculates **Most Likely = Best Case + 50%**. The Most Likely field is shown but locked so the user does not need to enter it manually.

A separate **Best Case Only** tab supports sparse input. Its documented planning heuristic is:

- best = user input
- worst = `2 × best`
- most likely = midpoint of best and worst

The app then calculates the weighted PERT mean, sigma, Wize Wizard 2σ aggressive/high-stress point, 3σ low-stress allowance, a 3-point vs 6-point recommendation, and a detailed confidence-ratio sentence.

The sparse-input method is explicitly a heuristic, not measured statistical variance.

## Communications

The Communications tab has a dedicated **Run Communications Report** action using:

`n(n-1)/2`

It reports raw communication lines, suggested grouping, internal lines, lead-to-lead lines, structured total, line reduction, percentage reduction, and a recommendation.

## Reports

The Reports / Charts tab currently generates terminal-native project Gantt/stress bars and PERT range summaries from saved estimates. All underlying data is persisted and exported.

## Install

```bash
cd wize-wizard
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
pip install -e .
wize-wizard
```

Database: `~/.local/share/wize-wizard/wize.db`

Press `Ctrl+E` to export the entire current project to `./wize-exports/<project-name>/` as CSV, JSON, and Markdown.


## v0.3 interaction fixes

- Most Likely is calculated as the midpoint of Best and Pessimistic. If Pessimistic is blank, Wize Wizard derives Pessimistic = 2×Best first.
- Pessimistic/Worst Case is optional: user-supplied values are honored; blank values use the documented 2×Best heuristic.
- START PERT REPORT calculates even without a selected project; an active project additionally saves the report.
- PERT output explains Best, Most Likely, Worst, range, weighted mean, sigma, Wize 2σ high-stress point, Wize 3σ low-stress allowance, severity, estimate-depth recommendation, confidence, and the range/box visualization.
- START COMMUNICATIONS REPORT calculates even without a selected project and now shows the complete n(n−1)/2 substitution, grouping model, internal channels, lead channels, reduction count, reduction percentage, and management interpretation.
- Best Case Only remains available as the separate sparse-input heuristic using Worst = 2×Best and Most Likely = midpoint.


## v0.4 PERT ranges
PERT reports now include approximate 68% (±1σ), 95% (±2σ), and 99.7% (±3σ) planning bands and explicitly show each upper allowance as expected time + sigma multiple. Each major TUI page also includes expanded usage instructions.

## v0.5 PERT envelope correction

Wize Wizard keeps standard three-point PERT for the expected duration and sigma:

- Expected = (Best + 4×Most Likely + Worst) / 6
- Sigma = (Worst − Best) / 6

The Wize planning envelopes expand outward from the full Best/Worst range:

- 68% / 1σ: max(0, Best − σ) to Worst + σ
- 95% / 2σ: max(0, Best − 2σ) to Worst + 2σ
- 99.7% / 3σ: max(0, Best − 3σ) to Worst + 3σ

No lower planning bound is allowed below zero. The maximum low-stress value is Worst + 3σ.

PERT reports are always persisted. If no project is selected, the app creates a Quick Analysis project automatically so Reports / Charts can immediately rebuild from the saved PERT record.
