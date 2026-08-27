#!/usr/bin/env bash
set -euo pipefail
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
mkdir -p "$HOME/bin"
cat > "$HOME/bin/wizard" <<WRAP
#!/usr/bin/env bash
exec "$PROJECT_DIR/scripts/deploy-richmackos.sh" "\$@"
WRAP
chmod +x "$HOME/bin/wizard"
case ":$PATH:" in
  *":$HOME/bin:"*) ;;
  *)
    printf '\nAdd this once if ~/bin is not already on PATH:\n  export PATH="$HOME/bin:$PATH"\n'
    ;;
esac
echo "Installed: $HOME/bin/wizard"
echo "Deploy with: wizard"
