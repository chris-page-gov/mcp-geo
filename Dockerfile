FROM python:3.11-slim

ARG HTTP_PROXY=""
ARG HTTPS_PROXY=""
ARG NO_PROXY=""
ARG http_proxy=""
ARG https_proxy=""
ARG no_proxy=""

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    ONS_LIVE_ENABLED=true \
    HTTP_PROXY=${HTTP_PROXY} \
    HTTPS_PROXY=${HTTPS_PROXY} \
    NO_PROXY=${NO_PROXY} \
    http_proxy=${http_proxy} \
    https_proxy=${https_proxy} \
    no_proxy=${no_proxy} \
    SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt \
    REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt \
    CURL_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt \
    PIP_CERT=/etc/ssl/certs/ca-certificates.crt

COPY .devcontainer/certs/ /tmp/docker-build-certs/
RUN set -eu; \
    mkdir -p /usr/local/share/ca-certificates/custom; \
    find /tmp/docker-build-certs -maxdepth 1 -type f -name "*.crt" \
        -exec cp {} /usr/local/share/ca-certificates/custom/ \; || true; \
    if command -v update-ca-certificates >/dev/null 2>&1; then \
        update-ca-certificates; \
    fi

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates \
    && update-ca-certificates \
    && rm -rf /tmp/docker-build-certs \
    && rm -rf /var/lib/apt/lists/*

COPY . /app

RUN rm -rf /app/.devcontainer/certs

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir .

RUN useradd --create-home --shell /bin/bash appuser \
    && chown -R appuser:appuser /app

USER appuser

CMD ["python", "-m", "server.stdio_adapter"]
