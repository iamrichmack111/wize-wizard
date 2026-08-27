# RichmackOS deployment — `wizard`

Production target:

- URL: `https://wizard.richmackos.com`
- Server directory: `/home/ubuntu/wizard`
- Backend: `127.0.0.1:5080`
- Container: `wizard`
- Persistent data: `/home/ubuntu/wizard/data`
- Health: `/healthz`

The deployment follows the RichmackOS production pattern: Route 53 first, rsync from the Mac, localhost-only Docker service, Nginx as the public entry point, then Certbot/TLS. Production `.env` and `data/` are never rsynced or deleted.

## Install the Mac command once

```bash
cd ~/Downloads/wize-wizard-main
./scripts/install-wizard-command.sh
```

If needed, add `~/bin` to `PATH`.

## One-command deployment

```bash
wizard
```

Useful read-only commands:

```bash
wizard status
wizard logs
wizard health
```

## SSH resilience

The deployer disables pseudo-terminal allocation (`ssh -T`), enables keepalives, retries transient SSH failures, and checks the real backend health before treating a non-zero SSH return code as deployment failure. If the SSH connection drops after Docker has already completed successfully, a healthy `/healthz` wins and the deployment continues.

## GitHub hardening and CI/CD

The `wizard` Mac-side command now runs `scripts/bootstrap-git.sh` before deployment.
On the first run it initializes Git when needed, verifies `.gitignore`, makes shell
scripts executable, performs a local secret preflight, creates an initial commit,
and, when GitHub CLI is authenticated, creates/uses a private `wize-wizard`
repository and pushes `main`.

The repository includes:

- `.github/workflows/ci.yml` — Python 3.10/3.12 tests, compile checks, package build, Docker build.
- `.github/workflows/security.yml` — Bandit, pip-audit, Trivy vulnerability/secret/misconfiguration scanning.
- `.github/workflows/codeql.yml` — GitHub CodeQL Python analysis.
- `.github/workflows/deploy.yml` — test/build gate, rsync to Lightsail, `richdeploy wizard`, SSH transport-failure recovery, backend/public health verification.
- `.github/dependabot.yml` — weekly Python and GitHub Actions dependency updates.

When `gh` is authenticated, bootstrap also attempts to install the RichmackOS
SSH deployment key and host/user as GitHub Actions secrets and enables GitHub
secret-scanning/push-protection and branch protection on a best-effort basis.

## Git transport

The bootstrap enforces an SSH GitHub origin (`git@github.com:OWNER/REPO.git`). If an existing GitHub origin uses HTTPS, it is converted to SSH before the first push. The bootstrap also sets `gh` to prefer SSH for future Git operations. GitHub Actions still uses its internal checkout mechanism, while production deployment itself uses SSH/rsync.
