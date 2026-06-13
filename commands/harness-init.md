---
description: Scaffold the repo-agent-harness (agent/ policies + tools, AGENTS.md) into the current repository.
argument-hint: "[--force] [--agents-md auto|skip|overwrite] [--pin <sha>]"
allowed-tools: Bash, Read, Edit
---

Set up the **repo-agent-harness** in the current repository so a coding agent has safe,
deterministic, repo-aware tooling. The heavy lifting is done by the harness's own CLI — do
not copy files by hand.

1. Confirm the working directory is inside a git repo: `git rev-parse --show-toplevel`.
2. Run the deterministic installer (pass through any flags the user gave:
   `--force`, `--agents-md auto|skip|overwrite`):

   ```bash
   HARNESS_SHA="ebff259fb41b4db6fefdcfda549303d08e20868f"   # repo-agent-harness main sha; keep in sync with /new-app and /harness-app
   uvx --from "git+https://github.com/astrojones/repo-agent-harness@${HARNESS_SHA}#subdirectory=mcp" \
     repo-agent-harness init --agents-md auto --json
   ```

   It installs `agent/` (policies, manifest, tools) and creates/refreshes `AGENTS.md`
   (marker-delimited section, idempotent). Existing files are never overwritten without
   `--force`. Report `created`/`merged`/`skipped` to the user.

   **Note:** the MCP server is bundled in the astrojones-dev plugin and auto-connects —
   no `.mcp.json` is written. If the user needs a project-pinned entry for CI or
   non-Claude-Code clients, re-run with `--pin "${HARNESS_SHA}"`.

3. Tailor `agent/manifest.yml` to this repo (name, frameworks, important paths,
   entrypoints) and review `agent/policies/` for project-specific allow/deny rules.
4. Tell the user the harness is ready. Run `agent/tools/repo-overview` to confirm it
   is working (requires an active session with the plugin loaded).

Keep edits minimal; the defaults are intentionally conservative.
