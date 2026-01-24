FROM mcr.microsoft.com/devcontainers/python:3.11

# Install CA certificates for SSL support and update trust store
RUN rm -f /etc/apt/sources.list.d/yarn.list || true && \
	find /etc/apt/sources.list.d -maxdepth 1 -type f -name "*.list" \
		-exec grep -l "dl.yarnpkg.com" {} + 2>/dev/null \
		| xargs -r rm -f || true && \
	apt-get update && \
	apt-get install -y --no-install-recommends ca-certificates curl && \
	update-ca-certificates && \
	rm -rf /var/lib/apt/lists/*

# Set workdir (optional, VS Code devcontainer will set this automatically)
WORKDIR /workspaces/mcp-geo


# Install Python dependencies globally (for CI and dev reliability)
RUN pip install fastapi uvicorn python-dotenv pydantic-settings --upgrade certifi

# Ensure requests uses certifi's CA bundle (set to actual path, no shell expansion)
ENV REQUESTS_CA_BUNDLE=/usr/local/lib/python3.11/site-packages/certifi/cacert.pem

# Install ngrok for HTTPS tunneling in devcontainer workflows
ARG NGROK_TARBALL_URL="https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz"
RUN curl -sSL "$NGROK_TARBALL_URL" -o /tmp/ngrok.tgz && \
	tar -xzf /tmp/ngrok.tgz -C /usr/local/bin && \
	rm /tmp/ngrok.tgz

# No CMD needed; VS Code devcontainer will handle the default command
