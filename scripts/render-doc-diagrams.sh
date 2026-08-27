#!/usr/bin/env bash
set -euo pipefail
ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"
command -v d2 >/dev/null || { echo "ERROR: install D2 first"; exit 1; }
mkdir -p docs/images/diagrams
for f in docs/diagrams/*.d2; do
  n="$(basename "$f" .d2)"
  echo "🎨 Rendering $n"
  d2 --layout elk --theme 200 "$f" "docs/images/diagrams/$n.svg"
  d2 --layout elk --theme 200 "$f" "docs/images/diagrams/$n.png"
done
echo "✅ Fancy D2 diagrams rendered"
