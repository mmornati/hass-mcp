"""Entry point for running Hass-MCP via uv/uvx tool"""

from app.server import run_server


def main():
    """Run the MCP server with transport selected via environment variables.

    Transport is configured through these environment variables:
        - MCP_TRANSPORT: Transport mode ("stdio", "sse", or "streamable-http").
                         Defaults to "stdio".
        - MCP_HOST: Host address to bind (default: "127.0.0.1").
        - MCP_PORT: Port to bind (default: "8000").
        - PORT: Alternative port variable (Smithery compatibility).
    """
    run_server()
