FROM python:3.11-slim
WORKDIR /workspaces/mcp-geo
COPY .. .
# Install CA certificates for SSL support
RUN apt-get update && apt-get install -y ca-certificates && update-ca-certificates
RUN pip install fastapi uvicorn python-dotenv pydantic-settings
CMD ["uvicorn", "server.main:app", "--host", "0.0.0.0", "--port", "8000"]
