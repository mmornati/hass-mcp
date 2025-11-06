# Multi-stage build for smaller final image (base image without VectorDB)
# Stage 1: Build stage with uv and build tools
FROM ghcr.io/astral-sh/uv:0.6.6-python3.13-bookworm AS builder

WORKDIR /app

# Copy project files
COPY . .

# Install package with UV (without vectordb dependencies for smaller image)
RUN uv pip install --system -e .

# Stage 2: Runtime stage with minimal base
FROM python:3.13-slim

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
WORKDIR /app
COPY . .

# Set environment for MCP communication
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Disable VectorDB by default for this base image
# Users can enable it by setting HASS_MCP_VECTOR_DB_ENABLED=true
# and connecting to an external VectorDB server
ENV HASS_MCP_VECTOR_DB_ENABLED=false

# Run the MCP server with stdio communication using the module directly
ENTRYPOINT ["python", "-m", "app"]
