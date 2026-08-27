#!/usr/bin/env bash
set -Eeuo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

say() { printf '\n\033[1;36m==> %s\033[0m\n' "$*"; }
warn() { printf '\n\033[1;33mWARN: %s\033[0m\n' "$*" >&2; }

if ! command -v git >/dev/null 2>&1; then
  warn 'git is not installed; skipping Git bootstrap.'
  exit 0
fi

if [[ ! -d .git ]]; then
  say 'Initializing local Git repository'
  git init
  git branch -M main
fi

# Never allow production state into source control.
touch .gitignore
for pattern in '.env' '.venv/' '__pycache__/' '*.pyc' '.pytest_cache/' 'data/' 'backups/' '*.db' '.DS_Store'; do
  grep -Fxq "$pattern" .gitignore || printf '%s\n' "$pattern" >> .gitignore
done

chmod +x scripts/*.sh 2>/dev/null || true

say 'Running local secret preflight'
# Scan tracked/candidate source, while avoiding documentation examples and the scanner itself.
if grep -RInE --exclude-dir=.git --exclude-dir=.venv --exclude='*.md' --exclude='*.txt' --exclude='bootstrap-git.sh' \
  '(BEGIN (RSA |OPENSSH )?PRIVATE KEY|AKIA[0-9A-Z]{16}|aws_secret_access_key[[:space:]]*=[[:space:]]*[A-Za-z0-9/+]{20,}|WIZE_SECRET_KEY[[:space:]]*=[[:space:]]*[A-Fa-f0-9]{32,})' .; then
  warn 'Potential secret material found. Review the lines above before committing.'
  exit 2
fi

git add .
if ! git diff --cached --quiet; then
  git commit -m "Harden Wize Wizard production baseline" || {
    warn 'Commit could not be created. Configure git user.name/user.email and rerun wizard.'
    exit 2
  }
fi

# Create/find a private GitHub repo, and ALWAYS use SSH for the Git remote.
# This intentionally avoids HTTPS credentials/tokens for normal git push/pull.
if command -v gh >/dev/null 2>&1 && gh auth status >/dev/null 2>&1; then
  OWNER="$(gh api user --jq .login)"
  REPO="wize-wizard"
  SSH_REMOTE="git@github.com:${OWNER}/${REPO}.git"

  if ! git remote get-url origin >/dev/null 2>&1; then
    say "Creating or attaching private GitHub repository ${OWNER}/${REPO} over SSH"
    if gh repo view "${OWNER}/${REPO}" >/dev/null 2>&1; then
      git remote add origin "$SSH_REMOTE"
    else
      # Create the repository without asking gh to choose the Git protocol, then attach SSH explicitly.
      gh repo create "${OWNER}/${REPO}" --private --source=.
      git remote add origin "$SSH_REMOTE"
    fi
  else
    current_origin="$(git remote get-url origin)"
    case "$current_origin" in
      https://github.com/*|http://github.com/*)
        say 'Converting existing GitHub origin from HTTPS to SSH'
        # Preserve the existing owner/repository when possible instead of silently changing repos.
        repo_path="${current_origin#*github.com/}"
        repo_path="${repo_path%.git}"
        git remote set-url origin "git@github.com:${repo_path}.git"
        ;;
    esac
  fi

  # Make gh itself prefer SSH for future git operations on this host.
  gh config set git_protocol ssh --host github.com >/dev/null 2>&1 || true
fi

if git remote get-url origin >/dev/null 2>&1; then
  origin_url="$(git remote get-url origin)"
  if [[ "$origin_url" == https://github.com/* || "$origin_url" == http://github.com/* ]]; then
    warn "Refusing GitHub HTTPS origin: $origin_url"
    warn 'Configure an SSH origin (git@github.com:OWNER/REPO.git) before deployment.'
    exit 2
  fi

  say "Pushing Git baseline over SSH: $origin_url"
  git push -u origin main || warn 'Git push failed; RichmackOS deployment can still continue.'

  if command -v gh >/dev/null 2>&1 && gh auth status >/dev/null 2>&1; then
    REPO_SLUG="$(gh repo view --json nameWithOwner --jq .nameWithOwner 2>/dev/null || true)"
    if [[ -n "$REPO_SLUG" ]]; then
      say 'Configuring RichmackOS GitHub Actions deployment secrets'
      [[ -f "$HOME/.ssh/richmackos_deploy" ]] && gh secret set RICHMACKOS_SSH_KEY -R "$REPO_SLUG" < "$HOME/.ssh/richmackos_deploy" || true
      gh secret set RICHMACKOS_HOST -R "$REPO_SLUG" -b '3.129.79.249' || true
      gh secret set RICHMACKOS_USER -R "$REPO_SLUG" -b 'ubuntu' || true

      # Best-effort GitHub hardening. These API features vary by repo/account plan.
      gh api -X PATCH "repos/$REPO_SLUG" \
        -F 'security_and_analysis[secret_scanning][status]=enabled' \
        -F 'security_and_analysis[secret_scanning_push_protection][status]=enabled' \
        >/dev/null 2>&1 || warn 'Secret scanning/push protection could not be enabled automatically.'

      protection_json="$(mktemp)"
      cat > "$protection_json" <<'JSON'
{"required_status_checks":null,"enforce_admins":false,"required_pull_request_reviews":null,"restrictions":null,"required_linear_history":true,"allow_force_pushes":false,"allow_deletions":false}
JSON
      gh api -X PUT "repos/$REPO_SLUG/branches/main/protection" \
        -H 'Accept: application/vnd.github+json' \
        --input "$protection_json" >/dev/null 2>&1 \
        || warn 'Branch protection could not be enabled automatically.'
      rm -f "$protection_json"
    fi
  fi
fi
