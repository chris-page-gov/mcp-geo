FROM mcr.microsoft.com/devcontainers/python:3.11

ARG HTTP_PROXY=""
ARG HTTPS_PROXY=""
ARG NO_PROXY=""
ARG http_proxy=""
ARG https_proxy=""
ARG no_proxy=""
ARG INSTALL_NGROK="false"
ARG NGROK_TARBALL_URL="https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz"

ENV SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt \
	REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt \
	CURL_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt \
	PIP_CERT=/etc/ssl/certs/ca-certificates.crt

COPY .devcontainer/certs/ /tmp/devcontainer-certs/
RUN set -eu; \
	mkdir -p /usr/local/share/ca-certificates/custom; \
	find /tmp/devcontainer-certs -maxdepth 1 -type f -name "*.crt" \
		-exec cp {} /usr/local/share/ca-certificates/custom/ \; || true; \
	if command -v update-ca-certificates >/dev/null 2>&1; then \
		update-ca-certificates; \
	fi

# Install CA certificates for SSL support and update trust store.
RUN HTTP_PROXY="${HTTP_PROXY}" HTTPS_PROXY="${HTTPS_PROXY}" NO_PROXY="${NO_PROXY}" \
	http_proxy="${http_proxy}" https_proxy="${https_proxy}" no_proxy="${no_proxy}" \
	rm -f /etc/apt/sources.list.d/yarn.list || true && \
	find /etc/apt/sources.list.d -maxdepth 1 -type f -name "*.list" \
		-exec grep -l "dl.yarnpkg.com" {} + 2>/dev/null \
		| xargs -r rm -f || true && \
	apt-get update && \
	apt-get install -y --no-install-recommends \
		ca-certificates \
		curl \
		build-essential \
		libpq-dev \
		pkg-config \
		gdal-bin \
		libgdal-dev \
		libgeos-dev \
		proj-bin \
		libproj-dev && \
	update-ca-certificates && \
	rm -rf /tmp/devcontainer-certs && \
	rm -rf /var/lib/apt/lists/*

# Set workdir (optional, VS Code devcontainer will set this automatically)
WORKDIR /workspaces/mcp-geo


# Install Python dependencies globally (for CI and dev reliability)
RUN HTTP_PROXY="${HTTP_PROXY}" HTTPS_PROXY="${HTTPS_PROXY}" NO_PROXY="${NO_PROXY}" \
	http_proxy="${http_proxy}" https_proxy="${https_proxy}" no_proxy="${no_proxy}" \
	pip install fastapi uvicorn python-dotenv pydantic-settings psycopg[binary] --upgrade certifi

# Install ngrok only when explicitly requested.
RUN if [ "$INSTALL_NGROK" = "true" ]; then \
		HTTP_PROXY="${HTTP_PROXY}" HTTPS_PROXY="${HTTPS_PROXY}" NO_PROXY="${NO_PROXY}" \
		http_proxy="${http_proxy}" https_proxy="${https_proxy}" no_proxy="${no_proxy}" \
		curl -sSL "$NGROK_TARBALL_URL" -o /tmp/ngrok.tgz && \
		tar -xzf /tmp/ngrok.tgz -C /usr/local/bin && \
		rm /tmp/ngrok.tgz; \
	else \
		echo "Skipping ngrok install (INSTALL_NGROK=$INSTALL_NGROK)."; \
	fi

# No CMD needed; VS Code devcontainer will handle the default command
