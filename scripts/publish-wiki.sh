#!/usr/bin/env bash
set -euo pipefail
ROOT="$(git rev-parse --show-toplevel)"
REPO="${WIZE_GITHUB_REPO:-iamrichmack111/wize-wizard}"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
cd "$TMP"
git clone "git@github.com:${REPO}.wiki.git" wiki
cd wiki
cp "$ROOT"/docs/wiki/*.md .
mkdir -p images/screenshots images/diagrams
cp "$ROOT"/docs/screenshots/qa/*.png images/screenshots/
cp "$ROOT"/docs/images/diagrams/*.png images/diagrams/ 2>/dev/null || true
cp "$ROOT"/docs/images/diagrams/*.svg images/diagrams/ 2>/dev/null || true
for page in *.md; do
  sed -i.bak 's#../screenshots/qa/#images/screenshots/#g; s#../images/diagrams/#images/diagrams/#g' "$page"
  rm -f "$page.bak"
done
python3 - <<'PY'
from pathlib import Path
import re, sys
bad=[]
for md in Path(".").glob("*.md"):
    for x in re.findall(r'!\[[^\]]*\]\(([^)]+)\)', md.read_text()):
        if not x.startswith(("http://","https://")) and not Path(x).exists():
            bad.append((md.name,x))
if bad:
    for a,b in bad: print("MISSING",a,b)
    sys.exit(1)
print("✅ Wiki image references verified")
PY
git add .
git diff --cached --quiet && { echo "✅ Wiki already current"; exit 0; }
git commit -m "Upgrade Wize Wizard visual documentation"
git push origin HEAD
echo "✅ Wiki published with screenshots and architecture images"
