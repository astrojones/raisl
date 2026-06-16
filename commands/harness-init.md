---
description: Explicit fallback to scaffold the agent harness (agent/ policies + tools, AGENTS.md, .opencode/opencode.json) into the current repository.
argument-hint: "[--force] [--agents-md auto|skip|overwrite] [--pin <sha>] [--target claude|opencode|both]"
allowed-tools: Bash, Read, Edit
---

Set up the **agent harness** in the current repository so a coding agent has safe,
deterministic, repo-aware tooling. The heavy lifting is done by the bundled harness CLI —
do not copy files by hand.

> **When you need this.** Connecting is zero-footprint — the server writes nothing into the
> repo by default, and the `repo_bootstrap` MCP tool is the in-session way to materialize it.
> Run this command when you want the on-disk harness without the MCP server: to edit per-repo
> `agent/` policies/health, to support a non-Claude-Code client (CI, opencode), or to
> force-overwrite, change the target surface, or refresh the opencode side.

1. Confirm the working directory is inside a git repo: `git rev-parse --show-toplevel`.
2. Run the bundled deterministic installer (it ships in this plugin — no network fetch).
   Pass through any flags the user gave (`--force`, `--agents-md auto|skip|overwrite`,
   `--pin <sha>`, `--target claude|opencode|both`):

   ```bash
   uv run --project "${CLAUDE_PLUGIN_ROOT}/servers/harness-mcp" \
     repo-agent-harness bootstrap --target both --json
   ```

   `bootstrap --target both` installs `agent/` (policies, manifest, tools), refreshes
   `AGENTS.md` (marker-delimited section, idempotent), and writes `.opencode/opencode.json`
   for opencode clients. Existing files are never overwritten without `--force`. Report
   `created`/`merged`/`skipped` to the user.

   **Note:** the MCP server is bundled in this plugin and auto-connects, so no `.mcp.json`
   is written by default — Claude Code users need nothing more. (`--pin` writes a
   project-pinned `.mcp.json` entry for CI / non-Claude-Code clients.)

3. Tailor `agent/manifest.yml` to this repo (name, frameworks, important paths,
   entrypoints) and review `agent/policies/` for project-specific allow/deny rules.
4. Tell the user the harness is ready. Run `agent/tools/repo-overview` to confirm it
   is working (requires an active session with the plugin loaded).

Keep edits minimal; the defaults are intentionally conservative.
