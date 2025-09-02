#!/bin/bash
# Update system CA certificates and Python certifi in WSL
set -e

sudo apt-get update
sudo apt-get install --reinstall -y ca-certificates
sudo update-ca-certificates

# Upgrade pip and certifi for all Python versions
if command -v python3 &>/dev/null; then
    python3 -m pip install --upgrade pip certifi || true
fi
if command -v python &>/dev/null; then
    python -m pip install --upgrade pip certifi || true
fi

echo "CA certificates and Python certifi updated. Please restart your shell or Python processes."
