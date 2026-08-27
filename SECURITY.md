# Security Policy

Do not report credentials in public issues. The built-in `admin/admin` credential exists only to bootstrap a new local installation and is flagged for immediate replacement. Production deployments must set a strong `WIZE_SECRET_KEY`, terminate TLS at a trusted reverse proxy, set `WIZE_SECURE_COOKIE=1`, protect the persistent database volume, and avoid exposing the service directly to the public Internet without HTTPS.
