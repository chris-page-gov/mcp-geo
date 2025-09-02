FROM mcr.microsoft.com/devcontainers/python:3.11

# Install CA certificates for SSL support and update trust store
RUN apt-get update && \
	apt-get install -y --no-install-recommends ca-certificates && \
	update-ca-certificates && \
	rm -rf /var/lib/apt/lists/*

# Set workdir (optional, VS Code devcontainer will set this automatically)
WORKDIR /workspaces/mcp-geo


# Install Python dependencies globally (for CI and dev reliability)
RUN pip install fastapi uvicorn python-dotenv pydantic-settings --upgrade certifi

# Ensure requests uses certifi's CA bundle (set to actual path, no shell expansion)
ENV REQUESTS_CA_BUNDLE=/usr/local/lib/python3.11/site-packages/certifi/cacert.pem

# No CMD needed; VS Code devcontainer will handle the default command
