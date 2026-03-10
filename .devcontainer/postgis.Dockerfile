FROM postgis/postgis:16-3.4

ARG HTTP_PROXY=""
ARG HTTPS_PROXY=""
ARG NO_PROXY=""
ARG http_proxy=""
ARG https_proxy=""
ARG no_proxy=""

COPY .devcontainer/certs/ /tmp/devcontainer-certs/
RUN set -eu; \
    mkdir -p /usr/local/share/ca-certificates/custom; \
    find /tmp/devcontainer-certs -maxdepth 1 -type f -name "*.crt" \
        -exec cp {} /usr/local/share/ca-certificates/custom/ \; || true; \
    if command -v update-ca-certificates >/dev/null 2>&1; then \
        update-ca-certificates; \
    fi

RUN HTTP_PROXY="${HTTP_PROXY}" HTTPS_PROXY="${HTTPS_PROXY}" NO_PROXY="${NO_PROXY}" \
    http_proxy="${http_proxy}" https_proxy="${https_proxy}" no_proxy="${no_proxy}" \
    apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        postgresql-16-pgrouting \
        postgresql-16-pgrouting-scripts \
    && update-ca-certificates \
    && rm -rf /tmp/devcontainer-certs \
    && rm -rf /var/lib/apt/lists/*
