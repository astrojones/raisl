#!/bin/bash
set -euo pipefail

# Only needed for Claude Code on the web; local dev uses `claude --plugin-dir`
# (see README "Local development").
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

claude plugin install raisl@astrojones || echo "raisl: plugin install failed, continuing without it" >&2
