#!/usr/bin/env bash
set -Eeuo pipefail

APP="wizard"
DOMAIN="wizard.richmackos.com"
SERVER="ubuntu@3.129.79.249"
SERVER_IP="3.129.79.249"
REMOTE_DIR="/home/ubuntu/wizard"
PORT="5080"
SSH_KEY="${HOME}/.ssh/richmackos_deploy"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SSH_OPTS=(
  -T
  -o IdentitiesOnly=yes
  -o ServerAliveInterval=15
  -o ServerAliveCountMax=6
  -o ConnectTimeout=12
  -o ConnectionAttempts=3
  -o TCPKeepAlive=yes
  -o LogLevel=ERROR
  -i "$SSH_KEY"
)

say() { printf '\n\033[1;36m==> %s\033[0m\n' "$*"; }
warn() { printf '\n\033[1;33mWARN: %s\033[0m\n' "$*" >&2; }
die() { printf '\n\033[1;31mERROR: %s\033[0m\n' "$*" >&2; exit 1; }

ssh_once() {
  ssh "${SSH_OPTS[@]}" "$SERVER" "$@"
}

# SSH can occasionally return non-zero when the transport drops even though the
# remote command completed. Retry transport failures, and let callers verify
# actual service health before treating a non-zero result as fatal.
ssh_retry() {
  local attempts="${SSH_ATTEMPTS:-3}" delay="${SSH_RETRY_DELAY:-3}" rc=0 i
  for ((i=1; i<=attempts; i++)); do
    if ssh_once "$@"; then
      return 0
    fi
    rc=$?
    warn "SSH attempt ${i}/${attempts} returned ${rc}; reconnecting in ${delay}s."
    sleep "$delay"
  done
  return "$rc"
}

remote_health() {
  ssh_once "curl -fsS --max-time 5 http://127.0.0.1:${PORT}/healthz >/dev/null" >/dev/null 2>&1
}

public_health() {
  curl -fsS --max-time 10 "https://${DOMAIN}/healthz" >/dev/null 2>&1
}

wait_remote_health() {
  local i
  for i in $(seq 1 35); do
    if remote_health; then
      return 0
    fi
    printf '.'
    sleep 2
  done
  printf '\n'
  return 1
}

case "${1:-deploy}" in
  status)
    ssh_retry "cd '$REMOTE_DIR' && docker compose -f docker-compose.prod.yml ps && echo && curl -fsS http://127.0.0.1:${PORT}/healthz" || true
    exit 0
    ;;
  logs)
    ssh_retry "cd '$REMOTE_DIR' && docker compose -f docker-compose.prod.yml logs --tail=150" || true
    exit 0
    ;;
  health)
    if public_health; then echo "wizard healthy: https://${DOMAIN}"; exit 0; fi
    die "Public health check failed: https://${DOMAIN}/healthz"
    ;;
  deploy|"") ;;
  *) die "Usage: wizard [deploy|status|logs|health]" ;;
esac

say "Git / GitHub production bootstrap"
"$PROJECT_DIR/scripts/bootstrap-git.sh" || die "Git hardening bootstrap failed. Fix the warning above, then rerun wizard."

command -v rsync >/dev/null || die "rsync is required on the Mac."
command -v curl >/dev/null || die "curl is required on the Mac."
command -v dig >/dev/null || die "dig is required on the Mac."
[[ -f "$SSH_KEY" ]] || die "Missing deployment key: $SSH_KEY"
chmod 600 "$SSH_KEY" 2>/dev/null || true

say "Checking SSH without allocating a terminal"
ssh_retry "printf 'connected: '; hostname" || die "Could not reach RichmackOS over SSH."

say "Ensuring DNS for ${DOMAIN}"
DNS_NOW="$(dig +short "$DOMAIN" A | tail -n1 || true)"
if [[ "$DNS_NOW" != "$SERVER_IP" ]]; then
  command -v r53sub >/dev/null || die "r53sub is not in PATH. Expected your RichmackOS helper on the Mac."
  r53sub -s wizard -i "$SERVER_IP" -t 300
  for i in $(seq 1 30); do
    DNS_NOW="$(dig +short "$DOMAIN" A | tail -n1 || true)"
    [[ "$DNS_NOW" == "$SERVER_IP" ]] && break
    sleep 2
  done
  [[ "$DNS_NOW" == "$SERVER_IP" ]] || die "DNS has not resolved to $SERVER_IP yet. Re-run 'wizard' after DNS propagates."
fi
echo "DNS: $DOMAIN -> $DNS_NOW"

say "Preparing production directory while preserving .env and data"
# The container runs as UID/GID 10001. A host-created bind mount owned by ubuntu/root
# is not writable by that user, which causes sqlite3.OperationalError: unable to open database file.
# Create/preserve the bind-mounted data directory and explicitly hand ownership to the
# container user before every deployment. Existing database contents are preserved.
ssh_retry "mkdir -p '$REMOTE_DIR/backups' && sudo mkdir -p '$REMOTE_DIR/data' && sudo chown -R 10001:10001 '$REMOTE_DIR/data' && sudo chmod 0750 '$REMOTE_DIR/data'" || die "Could not prepare writable production data directory."

# If port is busy, allow it only when our wizard container owns it.
PORT_STATE="$(ssh_once "if sudo ss -ltnp | grep -q ':${PORT} '; then if docker ps --format '{{.Names}}' | grep -qx wizard; then echo OWNED; else echo BUSY; fi; else echo FREE; fi" 2>/dev/null || true)"
[[ "$PORT_STATE" != "BUSY" ]] || die "Port ${PORT} is already in use by another service. No changes were made."
echo "Port ${PORT}: ${PORT_STATE:-unknown}"

say "Syncing code from the Mac"
rsync -az --delete \
  -e "ssh -T -o IdentitiesOnly=yes -o ServerAliveInterval=15 -o ServerAliveCountMax=6 -o ConnectTimeout=12 -o ConnectionAttempts=3 -i '$SSH_KEY'" \
  --exclude '.git/' \
  --exclude '.github/' \
  --exclude '.env' \
  --exclude 'data/' \
  --exclude 'backups/' \
  --exclude '.venv/' \
  --exclude '__pycache__/' \
  --exclude '.pytest_cache/' \
  --exclude '*.db' \
  "$PROJECT_DIR/" \
  "$SERVER:$REMOTE_DIR/"

say "Creating production secret only if this is the first deployment"
ssh_retry "cd '$REMOTE_DIR' && if [ ! -f .env ]; then umask 077; SECRET=\$(python3 -c 'import secrets; print(secrets.token_hex(32))'); printf 'WIZE_SECRET_KEY=%s\nWIZE_SECURE_COOKIE=1\n' \"\$SECRET\" > .env; echo 'created .env'; else echo 'preserved existing .env'; fi && mkdir -p data backups" || die "Could not create/preserve production environment."

say "Building and starting wizard"
DEPLOY_RC=0
ssh_once "cd '$REMOTE_DIR' && docker compose -f docker-compose.prod.yml up -d --build --remove-orphans" || DEPLOY_RC=$?
if [[ "$DEPLOY_RC" -ne 0 ]]; then
  warn "Initial SSH/deploy command returned ${DEPLOY_RC}. Checking real service state before declaring failure."
  sleep 3
  if remote_health; then
    warn "The SSH transport reported failure, but wizard is healthy. Continuing."
  else
    warn "Not healthy yet; retrying the deployment once after reconnect."
    ssh_retry "cd '$REMOTE_DIR' && docker compose -f docker-compose.prod.yml up -d --build --remove-orphans" || true
  fi
fi

say "Waiting for localhost health"
if ! wait_remote_health; then
  warn "Wizard did not become healthy. Showing status/logs."
  ssh_retry "cd '$REMOTE_DIR' && docker compose -f docker-compose.prod.yml ps; docker compose -f docker-compose.prod.yml logs --tail=150" || true
  die "Backend health failed after retries."
fi
echo "Backend healthy on 127.0.0.1:${PORT}"

say "Ensuring Nginx reverse proxy"
ssh_retry "if [ ! -f /etc/nginx/sites-available/${DOMAIN} ]; then sudo tee /etc/nginx/sites-available/${DOMAIN} >/dev/null <<'NGINX'
server {
    listen 80;
    listen [::]:80;
    server_name ${DOMAIN};
    location / {
        proxy_pass http://127.0.0.1:${PORT};
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_connect_timeout 30s;
        proxy_send_timeout 120s;
        proxy_read_timeout 120s;
    }
}
NGINX
sudo ln -sf /etc/nginx/sites-available/${DOMAIN} /etc/nginx/sites-enabled/${DOMAIN}; fi; sudo nginx -t && sudo systemctl reload nginx" || die "Nginx configuration failed."

say "Ensuring HTTPS certificate"
if ! ssh_once "sudo certbot certificates 2>/dev/null | grep -Fq '${DOMAIN}'" >/dev/null 2>&1; then
  ssh_retry "sudo certbot --nginx --non-interactive --agree-tos --redirect -m admin@richmackos.com -d '${DOMAIN}' && sudo nginx -t && sudo systemctl reload nginx" || die "Certbot failed. DNS is correct, so inspect certbot logs if this persists."
else
  echo "Existing certificate found; preserving it."
fi

say "Verifying public HTTPS"
for i in $(seq 1 15); do
  if public_health; then
    echo
    echo "=============================================="
    echo " WIZE WIZARD IS LIVE"
    echo " https://${DOMAIN}"
    echo "=============================================="
    exit 0
  fi
  printf '.'
  sleep 2
done
printf '\n'

# One final remote health check avoids reporting a deployment failure merely
# because the public TLS request raced Nginx/Certbot propagation.
if remote_health; then
  warn "Backend is healthy but public HTTPS did not verify yet. Deployment itself succeeded; check Nginx/TLS with 'wizard status'."
  exit 0
fi

die "Both public and backend health checks failed."
