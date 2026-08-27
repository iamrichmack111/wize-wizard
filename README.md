<<<<<<< HEAD
=======
# Wize Wizard v0.7.2 — Guided Strategy Learning + Original Core

Wize Wizard is a GUI + terminal strategy workbench designed for a user who may **not yet know what to do**. It preserves the original Wize mechanics and adds a guided learning layer around them.

The primary flow is:

```text
Learn (when needed)
  → Five Strategic Questions
  → I need to ___ so that I can ___
  → WHY? Wish → WHY? Dream → WHY? Fantasy
  → Need becomes the Goal
  → Original PERT / Stress assessment
  → Tasks / execution
  → Managed communications + supervisors
  → Market / finance / risk / operations analysis as needed
  → Clay Tablets + Journal
  → Final Project Plan and Scope
  → Repeat after execution
```

Every guided lesson spells out acronyms in full, explains the question the concept answers, provides plain-English meaning, a worked example, limitations, an interactive browser animation, and a corresponding Manim scene for production rendering. The bundled Strategy Handbook can be read inside the app. The **Final Project Plan** combines Goals, connected Whys, PERT ranges, tasks, team design, assumptions, recent learning, readiness gates, and handbook-based decision checks.

Temporary first-run credentials remain `admin` / `admin`; the account is forced to change the password after first login.

---

>>>>>>> 034f4b1 (Harden Wize Wizard production baseline)
# 🧙 Wize Wizard

> **Strategy • PERT • Execution**

**Wize Wizard** is a terminal-based strategic planning, decision-analysis, and execution system built with Python, Textual, and SQLite.

It combines structured strategic questioning, recursive Why analysis, PERT estimation, uncertainty ranges, stress-aware planning, communication-complexity analysis, task management, Clay Tablets, journaling, and project reporting inside a keyboard-friendly TUI.

The core idea is simple:

> **Turn strategy into structured reasoning, structured reasoning into measurable tasks, and measurable tasks into execution.**

---

## ✨ Features

### 🧠 Structured Strategy

Wize Wizard guides strategic planning through five core questions:

1. 🏆 **What is Winning?**
2. 🎯 **Where Will I Play?**
3. 🛠️ **What Tools Do I Need?**
4. 🧠 **What Skills Do I Need?**
5. ⚙️ **What Management Systems Do I Need?**

Every strategic statement follows a consistent grammar:

```text
As a ____________________________   [optional]

I need to _______________________
so that I can ___________________
because _________________________   [optional]
```

This creates structured records instead of disconnected journal entries.

---

## 🔍 Structured Why Analysis

Each strategy question automatically progresses through deeper levels of reasoning.

The user does **not** manually choose the level.

Wize Wizard manages the hierarchy internally:

```text
<<<<<<< HEAD
Initial Need
     ↓
Want
     ↓
Wish
     ↓
Dream
=======
Need / Goal
     ↓ WHY?
Wish
     ↓ WHY?
Dream
     ↓ WHY?
Fantasy
>>>>>>> 034f4b1 (Harden Wize Wizard production baseline)
```

Every level still uses the same structured grammar:

```text
As a ___

I need to ___
so that I can ___
because ___
```

### Example

```text
INITIAL NEED

As a software engineer,

I need to automate application deployment
so that I can release software consistently
because manual deployment introduces unnecessary variance.
```

Then:

```text
WANT

I need to standardize the deployment pipeline
so that I can make releases repeatable
because repeatability reduces operational uncertainty.
```

Then:

```text
WISH

I need to make infrastructure reproducible
so that I can recover and scale systems predictably
because infrastructure should behave as an engineered system.
```

Then:

```text
DREAM

I need to create self-managing delivery systems
so that I can focus on architecture instead of repetitive operations
because automation should increase strategic leverage.
```

---

## 🏺 Clay Tablets

Optional `because` statements are preserved in **Clay Tablets**.

Clay Tablets act as a project's reasoning and principles ledger.

A statement can therefore exist simultaneously as part of:

```text
Strategy
   │
<<<<<<< HEAD
   ├── Need / Want / Wish / Dream
=======
   ├── Need / Wish / Dream / Fantasy
>>>>>>> 034f4b1 (Harden Wize Wizard production baseline)
   │
   ├── Task
   │
   └── Clay Tablet
```

This makes it possible to retain not only **what** was decided, but **why** it was decided.

---

## ✅ Automatic Task Generation

Strategic statements can automatically become project tasks.

Additional manually created tasks follow the same Wize grammar:

```text
As a ____________________________

I need to _______________________
so that I can ___________________
because _________________________
```

This creates traceability from strategy to execution.

Conceptually:

```text
DREAM
  │
  ▼
WISH
  │
  ▼
WANT
  │
  ▼
NEED
  │
  ▼
TASK
  │
  ▼
PERT
  │
  ▼
EXECUTION
```

---

# 📐 PERT / Stress Analysis

Wize Wizard includes PERT-based schedule estimation with an additional planning-envelope interpretation.

The standard weighted PERT estimate is:

```text
Expected Time = (Best + 4 × Most Likely + Worst) / 6
```

Standard deviation is estimated as:

```text
σ = (Worst - Best) / 6
```

---

## ⏱️ Time Dimensions

PERT estimates can use multiple units:

```text
Minutes
Hours
Days
Weeks
Months
```

This allows the same analysis model to work for small operational tasks or long strategic projects.

---

## 📊 Best, Most Likely, and Pessimistic Estimates

When both Best and Pessimistic estimates are supplied:

```text
Best Case = user supplied
Worst Case = user supplied

Most Likely = midpoint(Best, Worst)
```

Example:

```text
Best Case:       5 hours
Pessimistic:    20 hours

Most Likely:

(5 + 20) / 2 = 12.5 hours
```

PERT then applies its weighted calculation:

```text
(5 + 4×12.5 + 20) / 6

= 12.5 hours
```

---

## 🧮 Missing Pessimistic Estimate

Sometimes only the Best Case is known.

Wize Wizard can create a planning estimate using:

```text
Pessimistic = Best Case × 2
```

Then:

```text
Most Likely =
(Best + Pessimistic) / 2
```

For example:

```text
Best Case = 10 hours

Derived Pessimistic:
10 × 2 = 20 hours

Most Likely:
(10 + 20) / 2 = 15 hours
```

⚠️ **Important:** A derived pessimistic estimate is a planning heuristic. It is not the same as collecting an independently estimated pessimistic value.

Wize Wizard identifies derived estimates in its reports.

---

# 📈 Sigma Planning Envelopes

Wize Wizard reports three uncertainty levels based on the calculated PERT sigma:

```text
1σ ≈ 68%
2σ ≈ 95%
3σ ≈ 99.7%
```

The Wize planning model expands these ranges outward from the **Best and Worst boundaries**.

### 1σ / ~68%

```text
Lower = Best - σ
Upper = Worst + σ
```

### 2σ / ~95%

```text
Lower = Best - 2σ
Upper = Worst + 2σ
```

### 3σ / ~99.7%

```text
Lower = Best - 3σ
Upper = Worst + 3σ
```

Time cannot fall below zero, so:

```text
Lower = max(0, calculated lower value)
```

---

## 🧪 Example Sigma Analysis

Suppose:

```text
Best Case = 5 hours
Worst Case = 20 hours
```

Then:

```text
σ = (20 - 5) / 6

σ = 2.5 hours
```

Wize Wizard produces:

```text
~68% / 1σ

5 - 2.5 → 20 + 2.5

2.5 → 22.5 hours
```

```text
~95% / 2σ

5 - 5 → 20 + 5

0 → 25 hours
```

```text
~99.7% / 3σ

5 - 7.5 → 20 + 7.5

0 → 27.5 hours
```

The lower boundary is clamped to zero:

```text
max(0, Best - nσ)
```

---

## 😌 Stress-Aware Planning

Wize Wizard uses the estimate envelope as a schedule-pressure aid.

A tighter schedule provides less temporal cushion.

A larger upper allowance provides more schedule flexibility.

Conceptually:

```text
AGGRESSIVE
    │
    │  Greater schedule pressure
    ▼

Expected
    │
    ├──── 1σ
    │
    ├──────── 2σ
    │
    └──────────── 3σ

                     LOW-STRESS
                     PLANNING EDGE
```

The 3σ upper boundary represents the largest displayed planning cushion:

```text
Worst + 3σ
```

This is a **Wize Wizard planning interpretation**, not a claim that a task is guaranteed to finish inside that interval.

---

# 🎯 Estimate Severity

Wize Wizard evaluates estimate uncertainty and recommends an appropriate estimation depth.

Possible recommendations include:

```text
3-point estimation
```

or:

```text
6-point estimation
```

Higher uncertainty, wider estimate spreads, or greater project severity can justify deeper estimation.

The goal is not simply to calculate a duration.

The goal is to understand:

```text
Duration
+
Uncertainty
+
Schedule pressure
+
Planning cushion
```

---

# 📊 Reports / Charts

PERT records are stored with their associated project.

The Reports / Charts section can use those records to generate terminal-native project visualizations.

Examples include:

### 📅 Stress-Aware Gantt View

```text
Architecture          ▓▓▓▓▓▓░░░░
Database              ▓▓▓▓▓▓▓▓░░░░
Testing               ▓▓▓▓▓░░░░░
Deployment            ▓▓▓░░░
```

Where:

```text
▓ = expected duration
░ = additional planning cushion
```

---

## 📦 Range Visualization

PERT ranges can also be represented as:

```text
Best
 │
 ├──────── Most Likely
 │               │
 │               ├──────── Worst
 │
 └────────────────────────────── 1σ
 └────────────────────────────────── 2σ
 └────────────────────────────────────── 3σ
```

This provides a visual representation of increasing schedule uncertainty.

---

# 👥 Communication Complexity

Wize Wizard includes communication-channel analysis using:

```text
n(n - 1)
────────
   2
```

where `n` is the number of people who may communicate directly with one another.

---

## 🧮 Example

For a 20-person team:

```text
20 × 19
───────
   2

= 190
```

That means there are potentially:

```text
190 communication channels
```

in a fully connected 20-person group.

---

# 🧩 Team Decomposition

Wize Wizard does more than display the raw communication count.

It can suggest breaking a large group into smaller units.

Example:

```text
20 people
```

might become:

```text
Team A — 5
Team B — 5
Team C — 5
Team D — 5
```

Internal channels per five-person group:

```text
5 × 4 / 2 = 10
```

Four teams:

```text
10 × 4 = 40
```

If four team leads communicate:

```text
4 × 3 / 2 = 6
```

Structured total:

```text
40 + 6 = 46 channels
```

Compared with:

```text
Unstructured: 190
Structured:    46
```

Potential reduction:

```text
144 communication relationships
```

or approximately:

```text
75.8%
```

This turns the communications formula into an organizational-design tool.

---

# 📉 Task Burndown

Wize Wizard tracks project execution through its task system.

Tasks can progress through statuses such as:

```text
Backlog
Ready
Active
Blocked
Done
```

The project can then display terminal-native burndown information.

Conceptually:

```text
Tasks

30 │●
27 │  ●
24 │    ●
21 │       ●
18 │          ●
15 │             ●
12 │                 ●
 9 │                    ●
 6 │                       ●
 3 │                          ●
 0 └────────────────────────────
```

---

# 📓 Journal

Wize Wizard includes a project journal for recording:

- 🧠 Decisions
- 📊 Estimation observations
- ⚠️ Risks
- 🛠️ Implementation notes
- 🔄 Strategy changes
- 📈 Outcomes
- 🧪 Experiments
- 📝 Retrospectives

The long-term goal is to connect planning assumptions with actual results.

For example:

```text
Estimated: 6 hours
Actual:    9 hours
Variance:  +3 hours
```

Historical information can eventually improve future estimation.

---

# 🗂️ Project Mode

Wize Wizard's major features are modular, but they can also operate together under a project.

```text
PROJECT
│
├── Strategy
│
├── Structured Whys
│
├── Wants
│
├── Wishes
│
├── Dreams
│
├── Tasks
│
├── PERT
│
├── Sigma Analysis
│
├── Communications
│
├── Reports / Charts
│
├── Clay Tablets
└── Journal
```

Records share project associations so related information can be grouped, analyzed, and exported together.

---

# 🧰 Modular Mode

Individual tools can also be used independently.

For example, you can use:

```text
PERT
```

without completing an entire strategic analysis.

Likewise:

```text
Communications
```

can be used as a standalone organizational-complexity calculator.

This gives Wize Wizard two operating philosophies:

```text
MODULAR MODE
Use the tool you need.
```

and:

```text
PROJECT MODE
Connect strategy → analysis → execution.
```

---

# 🏗️ Architecture

Wize Wizard is intentionally lightweight.

Core technologies:

- 🐍 **Python**
- 🖥️ **Textual**
- 🗃️ **SQLite**
- 📦 **Python packaging**
- 🧪 **PERT analysis**
- 📊 **Terminal-native reporting**

The application does not require a large external database server.

Project information is persisted locally using SQLite.

---

# 🗄️ Database

The local database is stored under the user's application-data directory.

Typical location:

```text
~/.local/share/wize-wizard/wize.db
```

The database stores project-related information such as:

```text
Projects
Strategies
Why statements
Clay Tablets
Tasks
PERT estimates
Communication analyses
Journal entries
```

---

# 📤 Export

Wize Wizard is designed around portable project data.

Supported or planned export formats include:

```text
JSON
CSV
Markdown
```

A project can therefore be represented outside the application for reporting, analysis, backup, or integration with other tools.

A complete project structure may contain:

```text
project-export/
├── project.md
├── strategy.md
├── tasks.csv
├── pert.csv
├── communications.csv
├── clay-tablets.md
├── journal.md
└── project.json
```

---

# 🚀 Installation

## Install from PyPI

Once published:

```bash
pip install wize-wizard
```

Launch:

```bash
wize-wizard
```

---

## 🧪 Recommended Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install wize-wizard
wize-wizard
```

---

# 💻 Install From Source

Clone the repository:

```bash
git clone git@github.com:iamrichmack111/wize-wizard.git
```

Enter the repository:

```bash
cd wize-wizard
```

Create a virtual environment:

```bash
python3 -m venv .venv
```

Activate it:

```bash
source .venv/bin/activate
```

Upgrade pip:

```bash
python -m pip install --upgrade pip
```

Install:

```bash
pip install -e .
```

Launch:

```bash
wize-wizard
```

---

# 🧪 Development

Install build and test tools:

```bash
python -m pip install -U build pytest twine
```

Compile-check:

```bash
python -m compileall -q .
```

Run tests:

```bash
pytest -q
```

Build distributions:

```bash
rm -rf dist build *.egg-info
python -m build
```

Validate distributions:

```bash
python -m twine check dist/*
```

---

# 📦 Packaging

A successful build should create:

```text
dist/
├── wize_wizard-X.Y.Z-py3-none-any.whl
└── wize_wizard-X.Y.Z.tar.gz
```

Test the wheel in a clean environment:

```bash
python3 -m venv /tmp/wize-test
source /tmp/wize-test/bin/activate
pip install dist/*.whl
wize-wizard
```

---

# ⚙️ CI/CD

Wize Wizard supports automated publishing through GitHub Actions and PyPI Trusted Publishing.

Example release flow:

```text
Development
     │
     ▼
Git Commit
     │
     ▼
GitHub
     │
     ▼
Version Tag
     │
     ▼
GitHub Release
     │
     ▼
GitHub Actions
     │
     ├── Build wheel
     ├── Build source distribution
     └── Publish
             │
             ▼
            PyPI
```

The publishing workflow lives at:

```text
.github/workflows/publish.yml
```

---

# 🏷️ Release Workflow

Example:

```bash
git add -A
git commit -m "Release Wize Wizard"
git push
```

Create a version tag:

```bash
git tag -a v0.5.1 -m "Wize Wizard v0.5.1"
git push origin v0.5.1
```

Create the GitHub Release:

```bash
gh release create v0.5.1 \
  --title "Wize Wizard v0.5.1" \
  --generate-notes
```

Monitor CI/CD:

```bash
gh run list --workflow=publish.yml --limit 5
```

---

# 🔬 Design Philosophy

Wize Wizard treats planning as a connected system.

A strategic decision should not disappear after it is written.

Instead:

```text
IDENTITY
   ↓
STRATEGY
   ↓
WHY
   ↓
WANT
   ↓
WISH
   ↓
DREAM
   ↓
TASK
   ↓
ESTIMATE
   ↓
UNCERTAINTY
   ↓
SCHEDULE
   ↓
EXECUTION
   ↓
REFLECTION
```

The objective is **traceability**.

At any point, a user should eventually be able to answer:

> **Why am I doing this task?**

and trace the answer back through the strategy that created it.

---

# 🗺️ Roadmap

Planned improvements include:

- 🧙 Guided full-project Wizard
- 📊 Richer terminal charts
- 📅 Dependency-aware Gantt planning
- 📉 Weighted burndown
- 🧮 Historical estimation accuracy
- 🔄 Estimated vs. actual duration analysis
- 🎯 Strategy-to-task traceability
- 🏺 Clay Tablet pattern discovery
- 🔍 Project-wide search
- 📑 Rich project reports
- 📤 Expanded export formats
- 🧠 Estimation-bias analysis
- ⚠️ Risk and dependency modeling
- 👥 More advanced team decomposition
- ⌨️ Expanded keyboard-first navigation

---

# ⚠️ Statistical Note

PERT and sigma calculations are planning tools.

The familiar:

```text
68%
95%
99.7%
```

values originate from the empirical rule for normally distributed observations.

Wize Wizard's outward expansion from:

```text
Best - nσ
```

through:

```text
Worst + nσ
```

is a **Wize Wizard planning-envelope model** layered on top of the PERT estimates.

It should therefore be interpreted as a decision-support and schedule-cushion framework rather than a guarantee that a task has exactly a stated probability of completing within a given boundary.

---

# 🔐 Data Philosophy

Wize Wizard is designed as a local-first terminal application.

SQLite provides a lightweight persistence layer without requiring a separate database server.

Users remain able to export their project information into portable formats.

---

# 🤝 Contributing

Issues, feature requests, testing, and pull requests are welcome.

When contributing:

```bash
git checkout -b feature/my-feature
```

Make and test your changes:

```bash
python -m compileall -q .
pytest -q
```

Commit:

```bash
git add -A
git commit -m "Add my feature"
```

Push:

```bash
git push -u origin feature/my-feature
```

Then open a pull request.

---

# 📜 License

Check the repository's `LICENSE` file for the current licensing terms.

---

# 🧙 Wize Wizard

```text
╔══════════════════════════════════════════════╗
║                 WIZE WIZARD                  ║
║                                              ║
║        Strategy • PERT • Execution           ║
║                                              ║
║   I need to __________________________       ║
║   so that I can ______________________       ║
║   because ____________________________       ║
║                                              ║
║              Strategy → Action               ║
╚══════════════════════════════════════════════╝
```

**Build the strategy. Understand the uncertainty. Execute the plan.**

<<<<<<< HEAD
=======

---

# 🌐 Production GUI + Learning Course

Wize Wizard now includes a Flask-based web GUI while preserving the original Textual TUI.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
export WIZE_SECRET_KEY="$(python -c 'import secrets; print(secrets.token_hex(32))')"
wize-wizard-web
```

Open `http://127.0.0.1:8080`.

**Temporary first login:** `admin` / `admin`. The account is flagged to require an immediate password change.

## GUI modules

### Original Wize core — preserved

The GUI is an extension of the original Textual workflow, not a replacement for it. The `wize-wizard` command still launches the original TUI. The `wize-wizard-web` command launches the GUI, where the original core now has first-class pages for:

- Lafley five-question Strategy + Whys workflow
- Automatic `Initial Need → Want → Wish → Dream` progression
- Structured `[As a ___,] I need to ___ so that I can ___ [because ___]` grammar
- Dedicated 5 Whys root-cause drill
- Original PERT / stress report and Best × 2 sparse-input heuristic
- Tasks / burndown with strategy-linked tasks
- Communications channel analysis
- Clay Tablets reasoning ledger
- Project journal and PERT reports

The learning course, Manim scenes, market/finance tools and Monte Carlo lab complement those workflows by explaining what the concepts mean, when to use them and why.

### Supporting strategy / learning modules

- Home command center with D2 architecture
- Guided learning course with plain-English explanations, actual process steps, formulas, worked examples, limitations and quizzes
- Strategy assumption lab
- Market Structure Lab for CR4 and HHI
- Value Creation Lab for ROIC, WACC and Economic Profit
- Monte Carlo risk lab
- Admin-only user management and self-service password changes
- CSRF protection, password hashing, security headers, SQLite WAL mode and health endpoint

## Manim animations

Manim is optional because it can require system-level multimedia dependencies.

```bash
pip install -e '.[animation]'
python scripts/render_lessons.py
```

Source scenes live in `animations/strategy_lessons.py`. The GUI remains fully usable without rendered videos and shows an instructional animation module placeholder.

## D2

The home architecture source is:

```text
wize_wizard/static/diagrams/home.d2
```

If D2 is installed, render it with:

```bash
d2 wize_wizard/static/diagrams/home.d2 wize_wizard/static/diagrams/home.svg
```

## Docker

```bash
cp .env.example .env
# replace WIZE_SECRET_KEY with a long random value
docker compose up --build -d
curl http://127.0.0.1:8080/healthz
```

For TLS behind a reverse proxy, set `WIZE_SECURE_COOKIE=1`.


## v0.7.2 design pass
The web UI uses a Fibonacci spacing scale (5/8/13/21/34/55px) and golden-ratio 61.8/38.2 content layouts to reduce visual density. The Monte Carlo lab is simplified to estimate + uncertainty + impact, with plain-language Typical/Safer/Very cautious outputs.

## RichmackOS one-command deployment

For the production `wizard.richmackos.com` deployment, install the Mac-side helper once:

```bash
./scripts/install-wizard-command.sh
```

Then deploy with:

```bash
wizard
```

The helper uses `ssh -T`, keepalives, reconnect/retry logic, and post-command health verification so a transient SSH/terminal disconnect is not automatically treated as an application deployment failure. See `docs/RICHMACKOS_DEPLOY.md`.

## Production hardening

This build ships with CI, CodeQL, Bandit, pip-audit, Trivy, Dependabot, Docker
build validation, a private-repository bootstrap path, and RichmackOS continuous
deployment. The Mac-side `wizard` command performs Git/GitHub bootstrap before
it touches production, then deploys to `wizard.richmackos.com` using the
localhost-container + Nginx pattern.
>>>>>>> 034f4b1 (Harden Wize Wizard production baseline)
