# Installation

## Source
```bash
git clone git@github.com:iamrichmack111/wize-wizard.git
cd wize-wizard
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
```

## Initial administrator
```bash
export WIZE_ADMIN_USERNAME=admin
read -rsp "Bootstrap password: " WIZE_ADMIN_PASSWORD
echo
export WIZE_ADMIN_PASSWORD
```
The bootstrap password must be at least 12 characters.

## Start
```bash
wize-wizard-web
```

## Docker
Create `.env`, protect it with `chmod 600 .env`, then run `docker compose up --build`. Production binds host `127.0.0.1:5080` to container port `8080` and persists `./data` to `/data`.
