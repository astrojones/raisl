---
name: pyproject-canon
description: Generate or upgrade a Python pyproject.toml using the user's accumulated canonical config — ruff preview rules, pylint limits, ty type checker, pydantic-everywhere policy, PEP 735 dev groups, google docstrings, ban-relative-imports, calibrated test per-file-ignores. Use whenever the user asks to "create a pyproject.toml", "set up a Python project's tooling", "fix/align/canonicalize my pyproject", "modernize ruff config", "switch from mypy to ty", or starts a fresh Python package/CLI/API/MCP/bot/uv-workspace. Also use when reviewing an existing pyproject.toml for drift from the user's standard.
---

# pyproject-canon

Generate a `pyproject.toml` that matches the user's accumulated production
config — distilled from `acg/handoff`, `tg-agent-mcp`, `discord-bot`,
`ACG-CLI-python`, `capability-select-abc`. The shape of these files has
converged; this skill captures that convergence and applies it to new or
drifting projects.

This is **not** a green-start project bootstrap (use `python-init` for that).
It only emits or rewrites `pyproject.toml`.

## Source of truth

The canonical config is the **`astrojones/standards`** repo:
`python/pyproject.canonical.toml` (the config),
`python/variants.md` (decision rules), `python/why-these-rules.md` (rationale).

Fetch the live file before rendering — it is authoritative:
`https://raw.githubusercontent.com/astrojones/standards/main/python/pyproject.canonical.toml`
(via WebFetch, or `gh api repos/astrojones/standards/contents/python/pyproject.canonical.toml`).
`references/canonical_pyproject.toml` here is an **offline fallback mirror only** —
if it disagrees with the repo, the repo wins. Do not edit the standard here;
edit it in `astrojones/standards`.

Highlights worth knowing without reading the file:

- **Build**: `hatchling`, `src/`-layout, `[dependency-groups] dev` (PEP 735, not `[project.optional-dependencies] dev`).
- **Ruff**: `preview = true`, ~35 rule families, calibrated `pylint` complexity ceilings, `ban-relative-imports = "all"`, google docstrings.
- **Pydantic-everywhere policy**: `ANN401` blocks `Any`; the rest (no raw `dict`/`list[dict]` across boundaries; construct models at call sites) is enforced in review.
- **ty** (Astral's strict type checker) replaces mypy. Three rules at error level.
- **Tests**: a calibrated `per-file-ignores` block for `tests/**/*.py` covering asserts, magic numbers, missing docstrings, broad bandit, etc. Don't trim it.
- **Pytest**: `minversion = "8.0"`, `asyncio_mode = "auto"`, `--strict-markers`, coverage on `src/`, `filterwarnings = ["error::DeprecationWarning"]`.

## How to use this skill

### Step 1 — figure out the shape

Look at the user's request and the working directory before asking anything:

1. Is there an existing `pyproject.toml`? Read it.
2. Project intent: library / cli / api / mcp / bot / workspace? Infer from imports, dep names, presence of `[project.scripts]`, `packages/*` directory, etc.
3. Python version? Check `.python-version`, existing `requires-python`, CI matrix.
4. Line length already in use? (100 vs 120)

If 2-3 of those are unambiguous, proceed. Only ask the user for axes that are genuinely unclear, and batch them into one question.

### Step 2 — read the canonical reference

Always fetch `astrojones/standards/python/pyproject.canonical.toml` (raw URL
above) before writing the file. The comments are the spec. Don't paraphrase
from memory — the rule lists and per-file-ignores have been calibrated and are
easy to subtly break. If the network is unavailable, fall back to the local
mirror `references/canonical_pyproject.toml` and note that you used the mirror.

Then read `astrojones/standards/python/variants.md` (or the local
`references/variants.md` mirror) to know which fields to vary and how.

### Step 3 — render and write

- Preserve project identity from any existing pyproject.toml: `name`,
  `version`, `description`, `authors`, runtime `dependencies`,
  `[project.scripts]`, `[project.urls]`, `[tool.hatch.version]`, etc.
- Replace tooling sections wholesale (`[tool.ruff]`, `[tool.ty]`,
  `[tool.pytest.ini_options]`, `[tool.coverage.*]`, `[dependency-groups]`).
  Don't merge — partial adoption breaks rule interactions (e.g. the `D` rules
  need the per-file-ignores list to remain usable in tests).
- Apply variants per `references/variants.md`:
  - `target-version` and `requires-python` from the chosen Python version
  - Add `FAST` to ruff `select` if the project is a fastapi service
  - Use loose `[tool.ty.rules]` for bot projects with dynamic attribute access (cogs, settings)
  - Replace `[tool.hatch.*]` with `[tool.uv.workspace]` + `[tool.uv.sources]` for workspaces
  - Add `respx>=0.21` to dev group if tests mock httpx

### Step 4 — sanity check

After writing, check:

- `requires-python` and `target-version` agree (e.g. `>=3.13` ↔ `py313`)
- If `FAST` rule is selected, fastapi is in deps
- `[dependency-groups] dev` is present; there is no `[project.optional-dependencies] dev`
- `preview = true` is set under `[tool.ruff.lint]`
- `ban-relative-imports = "all"` and `convention = "google"` are present
- `[tool.ty.rules]` is present (not `[tool.mypy]`)

If the project uses `uv`, suggest running `uv sync` to verify resolution. If
ruff is installed, suggest `uv run ruff check .` to confirm the rules parse.

## What to refuse / replace silently

These show up in old configs the user has moved past. Replace without asking:

- **mypy** → `ty` (the user has migrated)
- **black** → drop (covered by `ruff format`)
- **`[project.optional-dependencies] dev`** → `[dependency-groups] dev`
- **Pinned `==` versions in runtime `dependencies`** → floor with `>=`
- **`select = [...]` without `preview = true`** → enable preview
- **`Any` in public signatures** / **`dict` crossing public boundaries** → flag in the response; the lint will catch it

## When NOT to use this skill

- The user wants a whole new project scaffolded (Dockerfile, README, src/, GHA workflow). Use `python-init` instead.
- The user is explicitly working in a non-Python ecosystem.
- The repo is on a legacy stack the user has decided not to migrate (e.g. a fork they don't own).
