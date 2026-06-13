# Decisions: when to default, when to ask

The canonical config converged across the user's recent projects. Most of it
is non-negotiable — apply without asking. A small set of axes legitimately
varies; ask only those.

## Default silently (do NOT ask)

These are stable across `acg/handoff`, `tg-agent-mcp`, `discord-bot`,
`ACG-CLI-python`, `capability-select-abc`. If you find yourself omitting one,
re-justify why.

- `hatchling` build backend with `src/`-layout
- `[dependency-groups] dev` (PEP 735), not `[project.optional-dependencies] dev`
- Dev group versions: `pytest>=8.3, pytest-asyncio>=0.24, pytest-cov>=5.0, ruff>=0.9, ty>=0.0.29, pre-commit>=4.0`
- Ruff `preview = true`
- The full canonical rule list (see `canonical_pyproject.toml`)
- Ruff `ignore = ["PLC0415", "RUF100"]`
- mccabe `max-complexity = 10`
- pylint limits: `max-args=5, max-positional-args=5, max-statements=50, max-branches=12, max-returns=6, max-nested-blocks=5`
- `ban-relative-imports = "all"`
- `pydocstyle.convention = "google"`
- `raises-extend-require-match-for` canonical list (ValidationError ×2, AttributeError, FileNotFoundError, asyncio.CancelledError)
- `[tool.ruff.lint.per-file-ignores]` for `tests/**/*.py` — the canonical list
- `[tool.ty.rules]`: `unresolved-import = "error"`, `unresolved-reference = "error"`, `invalid-assignment = "error"`
- `[tool.pytest.ini_options]`: `minversion = "8.0"`, `asyncio_mode = "auto"`, `--strict-markers`, `--cov=src`, `--cov-report=term-missing`
- `[tool.coverage.report]`: `precision = 2, show_missing = true, skip_covered = false`
- `[tool.coverage.run] omit = ["*/tests/*", "*/migrations/*"]`

## Variation axes (ask if not inferable)

Infer from context first — only ask if there's no clear signal. Use a single
batched AskUserQuestion if more than one axis is unclear.

### 1. Python version → `requires-python` + `target-version`
- Signals: existing `.python-version`, CI matrix, dependency floors (e.g. discord.py 2.6 needs ≥3.10).
- Defaults: **3.14** if unspecified. Fall back to **3.13** only when a required dep isn't 3.14-compatible yet (verify with `uv sync`). **3.11** only if they explicitly need broader compat.
- Map: `3.11 → py311`, `3.13 → py313`, `3.14 → py314`.

### 2. Line length
- **120** is the user's standard (acg-cli, ACGuild, handoff, tg-agent-mcp, discord-bot, agent).
- **100** only when matching an existing repo that uses it (`capability-select-abc`).
- Default 120; don't ask unless aligning to an existing repo.

### 3. Project shape → which template branch
Pick one based on project intent. Ask only if intent is genuinely ambiguous.

| Shape       | Signals                                       | Adds                                                           |
|-------------|-----------------------------------------------|----------------------------------------------------------------|
| `library`   | publishable, no entrypoint                    | base canonical only                                            |
| `cli`       | `[project.scripts]`, typer/click in deps      | `typer>=0.15`, `rich>=13.0`, `[project.scripts]` entrypoint    |
| `api`       | fastapi, uvicorn, route handlers              | `fastapi`, `uvicorn`, `httpx` in deps; **add `FAST` ruff rule** |
| `mcp`       | fastmcp/mcp servers                           | `fastmcp>=3.0`, `mcp>=1.20`                                    |
| `bot`       | discord.py, aiogram, telethon                 | bot framework dep; **`[tool.ty.rules]` loose variant** (cogs use dynamic attrs) |
| `workspace` | uv workspace with multiple `packages/*`       | replace `[tool.hatch.*]` with `[tool.uv.workspace]` + `[tool.uv.sources]` |

### 4. Pytest filterwarnings strictness
- **`["error::DeprecationWarning"]`** (default) — handoff, tg-agent-mcp, capability-select-abc style. Aggressive on deprecations only.
- **Strict variant** — `discord-bot` style:
  ```toml
  filterwarnings = ["error", "ignore::ResourceWarning", "ignore::pytest.PytestUnraisableExceptionWarning"]
  ```
  Use when the project has been hardened and you want every warning to fail tests. Don't ask; only switch on explicit user request.

### 5. Coverage HTML report
- Off by default (`--cov-report=term-missing` only).
- On (`--cov-report=html`) when project has CI artifact upload or user asked for HTML coverage. discord-bot uses it.

### 6. Parallel test execution
- Off by default.
- On (`-n auto --dist loadfile` + `pytest-xdist` in dev group) when the test suite is slow or the user explicitly asks. discord-bot uses it.

### 7. ty strictness
- **Strict** (default): three `error` rules only.
- **Loose** for bot/cog projects with dynamic attribute access (discord-bot pattern):
  ```toml
  possibly-missing-attribute = "ignore"
  unused-ignore-comment = "ignore"
  invalid-argument-type = "ignore"
  unresolved-attribute = "warn"
  missing-argument = "warn"
  ```

## Anti-patterns (refuse silently)

If the existing pyproject.toml or user request includes any of these, replace
with the canonical equivalent:

- **mypy** → use `ty` instead. The user moved off mypy.
- **black** → not needed; `ruff format` covers it.
- **`select` without `preview = true`** → enable preview; the rule set depends on it.
- **Pinned exact versions in `dependencies`** (e.g. `pydantic==2.9.2`) → use floors (`>=2.9`).
  Exception: `[dependency-groups] dev` versions are floors (`>=`), not pins.
- **`[project.optional-dependencies] dev = […]`** → move to `[dependency-groups] dev`.
- **Relative imports in source** → `ban-relative-imports = "all"` enforces this.
- **`Any` in public function signatures** → ANN401 blocks; use Pydantic models at boundaries.
- **`dict` / `list[dict]` crossing public function boundaries** → use Pydantic models.

## Authoring rule

When updating an existing pyproject.toml, **preserve the project's name,
version, description, and authors**. Replace the tooling sections wholesale.
Don't merge — the canonical config is internally consistent and partial
adoption breaks rule interactions (e.g. `D` rules need the per-file-ignores
list to be usable in tests).
