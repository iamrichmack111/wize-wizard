FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 WIZE_HOST=0.0.0.0 WIZE_PORT=8080 WIZE_SECURE_COOKIE=0
WORKDIR /app
RUN useradd --create-home --uid 10001 wize
COPY . /app
RUN pip install --no-cache-dir .
RUN mkdir -p /data && chown -R wize:wize /data /app
USER wize
ENV WIZE_DB_PATH=/data/wize.db
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/healthz',timeout=2)"
CMD ["wize-wizard-web"]
