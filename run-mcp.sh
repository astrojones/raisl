#!/usr/bin/env bash
# Launcher for the bundled repo-agent-harness MCP server.
# $0 is resolved to the plugin cache directory by the shell, so dirname gives the plugin root.
exec uv run --project "$(dirname "$0")/servers/harness-mcp" repo-agent-harness-mcp "$@"
