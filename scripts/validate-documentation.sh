#!/usr/bin/env bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
python -m compileall -q wize_wizard
python -m pytest -q
command -v bandit >/dev/null && bandit -r wize_wizard -ll -ii || true
python -c 'import pip_audit' >/dev/null 2>&1 && python -m pip_audit || echo "WARN: pip-audit not installed locally"
! grep -RIn --exclude-dir=.git --exclude-dir=.venv --exclude-dir=venv -E '^(<<<<<<<|=======|>>>>>>>)' .
for i in docs/screenshots/qa/03-strategy.png docs/screenshots/qa/04-strategic-questions-whys.png docs/screenshots/qa/05-pert-stress.png docs/screenshots/qa/06-communications.png docs/screenshots/qa/07-12-lessons.png docs/screenshots/qa/12-final-project-plan.png docs/screenshots/qa/90-mobile-home.png; do test -f "$i" || { echo "missing $i"; exit 1; }; done
git diff --check
echo "✅ documentation validation passed"
