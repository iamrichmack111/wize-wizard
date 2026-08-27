#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

if [ -z "${WIZARD_QA_PASSWORD:-}" ]; then
  read -rsp "Wizard admin password: " WIZARD_QA_PASSWORD
  echo
  export WIZARD_QA_PASSWORD
fi

python3 -m pip install -q playwright
python3 -m playwright install chromium

python3 wizard_playwright_qa.py

echo
echo "Open:"
echo "  docs/screenshots/qa/QA_REPORT.md"
