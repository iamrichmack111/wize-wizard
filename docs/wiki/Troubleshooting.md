# Troubleshooting

## Health
```bash
curl -fsS http://127.0.0.1:5080/healthz
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs --tail=120
```

## Fresh database
Set `WIZE_ADMIN_USERNAME` and `WIZE_ADMIN_PASSWORD`; password minimum is 12 characters.

## Data permissions
The production container runs as UID/GID 10001.
